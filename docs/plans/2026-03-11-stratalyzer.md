# Stratalyzer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** CLI tool that ingests a folder of downloaded influencer content (videos + images), transcribes/reads everything, groups by post, and synthesizes a structured machine-readable strategy document.

**Architecture:** Three-stage pipeline. Stage 1: extract (Whisper for video audio, Claude Vision for images). Stage 2: group files into posts by shared post ID in filename, produce per-post summaries. Stage 3: synthesize all post summaries into a single structured strategy document via LLM. Results cached at each stage so re-runs skip completed work.

**Tech Stack:** Python 3.14, Click (CLI), Rich (progress/output), Whisper (local transcription), Anthropic Claude API (vision + synthesis), Pydantic (data models), ffmpeg (audio extraction)

---

### Task 1: Project scaffolding + data models

**Files:**
- Create: `src/stratalyzer/__init__.py`
- Create: `src/stratalyzer/models.py`
- Create: `src/stratalyzer/cli.py`
- Create: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "stratalyzer"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "pydantic>=2.0",
    "anthropic>=0.40",
    "openai-whisper>=20240930",
    "pillow>=10.0",
]

[project.scripts]
stratalyzer = "stratalyzer.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Create data models in `src/stratalyzer/models.py`**

The filename pattern is: `{username}_{unix_timestamp}_{post_id}_{user_id}_{index}.{ext}`

Files sharing the same `post_id` belong to the same Instagram post (carousel or multi-clip reel).

```python
from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel


class MediaFile(BaseModel):
    """Single downloaded file (image or video)."""
    path: Path
    username: str
    timestamp: int
    post_id: str
    user_id: str
    index: int
    ext: str

    @classmethod
    def from_filename(cls, path: Path) -> MediaFile:
        stem = path.stem
        parts = stem.split("_")
        # username_timestamp_postid_userid_index
        # username may contain underscores, but we know:
        # - last part = index
        # - second to last = user_id
        # - third to last = post_id
        # - fourth to last = timestamp
        # - everything before that = username
        idx = int(parts[-1])
        user_id = parts[-2]
        post_id = parts[-3]
        timestamp = int(parts[-4])
        username = "_".join(parts[:-4])
        return cls(
            path=path,
            username=username,
            timestamp=timestamp,
            post_id=post_id,
            user_id=user_id,
            index=idx,
            ext=path.suffix.lstrip(".").lower(),
        )

    @property
    def is_video(self) -> bool:
        return self.ext in ("mp4", "mov", "webm")

    @property
    def is_image(self) -> bool:
        return self.ext in ("jpg", "jpeg", "png", "webp")


class Extraction(BaseModel):
    """Extracted content from a single media file."""
    file: str  # filename
    media_type: str  # "video" or "image"
    transcript: str | None = None  # whisper transcript (videos)
    vision_text: str | None = None  # text read from image (carousels)
    vision_description: str | None = None  # what the image shows
    is_educational: bool = False  # does this contain teaching content?


class PostSummary(BaseModel):
    """Aggregated content from one Instagram post (all carousel slides / clips)."""
    post_id: str
    username: str
    timestamp: int
    num_images: int
    num_videos: int
    extractions: list[Extraction]
    summary: str  # LLM-generated summary of what this post teaches
    topics: list[str]  # key topics covered
    is_educational: bool  # does this post contain teaching content?


class StrategyDocument(BaseModel):
    """Final synthesized output - the machine-readable strategy."""
    influencer: str
    total_posts: int
    educational_posts: int
    topics: dict[str, list[str]]  # topic -> list of key points
    processes: list[Process]
    frameworks: list[Framework]
    raw_post_summaries: list[PostSummary]


class Process(BaseModel):
    """A step-by-step process the influencer teaches."""
    name: str
    description: str
    steps: list[str]
    source_posts: list[str]  # post_ids where this was taught


class Framework(BaseModel):
    """A conceptual framework or mental model the influencer uses."""
    name: str
    description: str
    components: list[str]
    source_posts: list[str]
```

**Step 3: Write tests for filename parsing**

```python
from pathlib import Path
from stratalyzer.models import MediaFile


def test_parse_filename_jpg():
    p = Path("iamchrischung_1762530570_3760701455611845401_17814358_7.jpg")
    m = MediaFile.from_filename(p)
    assert m.username == "iamchrischung"
    assert m.timestamp == 1762530570
    assert m.post_id == "3760701455611845401"
    assert m.user_id == "17814358"
    assert m.index == 7
    assert m.ext == "jpg"
    assert m.is_image
    assert not m.is_video


def test_parse_filename_mp4():
    p = Path("iamchrischung_1772628983_3845412592060005965_17814358_1.mp4")
    m = MediaFile.from_filename(p)
    assert m.username == "iamchrischung"
    assert m.timestamp == 1772628983
    assert m.ext == "mp4"
    assert m.is_video
    assert not m.is_image
```

**Step 4: Create minimal CLI skeleton in `src/stratalyzer/cli.py`**

```python
import click

@click.group()
def main():
    """Stratalyzer - Extract strategies from influencer content."""
    pass

@main.command()
@click.argument("folder", type=click.Path(exists=True))
def analyze(folder: str):
    """Analyze a folder of influencer content."""
    click.echo(f"Analyzing {folder}...")
```

**Step 5: Run tests**

```bash
cd C:/Users/asus/Desktop/projects/stratalyzer
pip install -e .
pytest tests/test_models.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git init
git add pyproject.toml src/ tests/
git commit -m "feat: project scaffolding with data models and filename parser"
```

---

### Task 2: Folder scanner - discover and group files by post

**Files:**
- Create: `src/stratalyzer/scanner.py`
- Create: `tests/test_scanner.py`

**Step 1: Write the failing test**

```python
import tempfile
from pathlib import Path
from stratalyzer.scanner import scan_folder


def test_scan_groups_by_post():
    with tempfile.TemporaryDirectory() as d:
        # Two files from same post (same post_id)
        Path(d, "user_100_999_123_1.jpg").touch()
        Path(d, "user_100_999_123_2.jpg").touch()
        # One file from different post
        Path(d, "user_200_888_123_1.mp4").touch()
        # Non-media file should be ignored
        Path(d, "readme.txt").touch()

        posts = scan_folder(d)
        assert len(posts) == 2
        post_999 = next(p for p in posts if p[0].post_id == "999")
        assert len(post_999) == 2
        # Files should be sorted by index
        assert post_999[0].index == 1
        assert post_999[1].index == 2


def test_scan_empty_folder():
    with tempfile.TemporaryDirectory() as d:
        posts = scan_folder(d)
        assert len(posts) == 0
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_scanner.py -v
```
Expected: FAIL (scanner module doesn't exist)

**Step 3: Implement scanner**

```python
from pathlib import Path
from collections import defaultdict
from stratalyzer.models import MediaFile

MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm"}


def scan_folder(folder: str | Path) -> list[list[MediaFile]]:
    """Scan folder, return files grouped by post_id, sorted by index."""
    folder = Path(folder)
    groups: dict[str, list[MediaFile]] = defaultdict(list)

    for f in folder.iterdir():
        if not f.is_file() or f.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        try:
            media = MediaFile.from_filename(f)
            groups[media.post_id].append(media)
        except (ValueError, IndexError):
            continue  # skip files that don't match the naming pattern

    # Sort each group by index, then sort groups by timestamp (earliest first)
    result = []
    for post_id, files in groups.items():
        files.sort(key=lambda m: m.index)
        result.append(files)

    result.sort(key=lambda g: g[0].timestamp)
    return result
```

**Step 4: Run tests**

```bash
pytest tests/test_scanner.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add src/stratalyzer/scanner.py tests/test_scanner.py
git commit -m "feat: folder scanner groups media files by post"
```

---

### Task 3: Video transcription with Whisper

**Files:**
- Create: `src/stratalyzer/transcriber.py`
- Create: `tests/test_transcriber.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
from stratalyzer.transcriber import transcribe_video

# Use an actual video from the test data
TEST_VIDEO = Path("iamchrischung/iamchrischung_1772628983_3845412592060005965_17814358_1.mp4")


def test_transcribe_returns_string():
    if not TEST_VIDEO.exists():
        import pytest
        pytest.skip("Test video not available")
    result = transcribe_video(TEST_VIDEO)
    assert isinstance(result, str)
    # Could be empty if no speech, but should not error
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_transcriber.py -v
```
Expected: FAIL (module doesn't exist)

**Step 3: Implement transcriber**

Uses Whisper locally. Extracts audio with ffmpeg first (Whisper can handle mp4 directly, but explicit extraction is more reliable across formats).

```python
import subprocess
import tempfile
from pathlib import Path
import whisper

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


def transcribe_video(video_path: Path) -> str:
    """Transcribe a video file using Whisper. Returns transcript text."""
    model = _get_model()
    result = model.transcribe(str(video_path), language="en")
    return result["text"].strip()
```

**Step 4: Run test**

```bash
pytest tests/test_transcriber.py -v
```
Expected: PASS (may take a moment for Whisper model download on first run)

**Step 5: Commit**

```bash
git add src/stratalyzer/transcriber.py tests/test_transcriber.py
git commit -m "feat: video transcription with local Whisper"
```

---

### Task 4: Image analysis with Claude Vision

**Files:**
- Create: `src/stratalyzer/vision.py`
- Create: `tests/test_vision.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
from stratalyzer.vision import analyze_image

# Use actual carousel slide with text
TEST_IMAGE = Path("iamchrischung/iamchrischung_1762530570_3760701455611845401_17814358_7.jpg")


def test_analyze_image_returns_extraction():
    if not TEST_IMAGE.exists():
        import pytest
        pytest.skip("Test image not available")
    result = analyze_image(TEST_IMAGE)
    assert "text" in result
    assert "description" in result
    assert "is_educational" in result
    assert isinstance(result["is_educational"], bool)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_vision.py -v
```
Expected: FAIL

**Step 3: Implement vision analyzer**

Sends image to Claude with a prompt that extracts text and classifies content type. Uses base64 encoding.

```python
import base64
import json
from pathlib import Path
from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


VISION_PROMPT = """Analyze this Instagram post image. Return a JSON object with exactly these fields:

{
  "text": "all text visible in the image, transcribed exactly",
  "description": "brief description of what the image shows (1-2 sentences)",
  "is_educational": true/false (does this image teach something, share a framework, give advice, or contain instructional text?)
}

If there is no visible text, set "text" to "".
Return ONLY the JSON object, no other text."""


def analyze_image(image_path: Path) -> dict:
    """Analyze an image using Claude Vision. Returns dict with text, description, is_educational."""
    client = _get_client()
    data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    suffix = image_path.suffix.lower().lstrip(".")
    media_type = f"image/{'jpeg' if suffix in ('jpg', 'jpeg') else suffix}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)
```

**Step 4: Run test**

```bash
pytest tests/test_vision.py -v
```
Expected: PASS (requires ANTHROPIC_API_KEY in environment)

**Step 5: Commit**

```bash
git add src/stratalyzer/vision.py tests/test_vision.py
git commit -m "feat: image analysis with Claude Vision API"
```

---

### Task 5: Extraction pipeline with caching

**Files:**
- Create: `src/stratalyzer/extractor.py`
- Create: `tests/test_extractor.py`

This is the core pipeline: takes grouped posts from scanner, runs transcription on videos and vision on images, caches results to JSON so re-runs don't re-process.

**Step 1: Write the failing test**

```python
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from stratalyzer.extractor import extract_post, load_cache, save_cache
from stratalyzer.models import MediaFile


def test_cache_round_trip():
    with tempfile.TemporaryDirectory() as d:
        cache_path = Path(d) / "cache.json"
        save_cache(cache_path, {"file1.jpg": {"text": "hello"}})
        data = load_cache(cache_path)
        assert data["file1.jpg"]["text"] == "hello"


def test_cache_missing_file():
    data = load_cache(Path("/nonexistent/cache.json"))
    assert data == {}
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_extractor.py -v
```

**Step 3: Implement extractor**

```python
import json
from pathlib import Path
from rich.progress import Progress, TaskID
from stratalyzer.models import MediaFile, Extraction
from stratalyzer.transcriber import transcribe_video
from stratalyzer.vision import analyze_image

CACHE_FILENAME = ".stratalyzer_cache.json"


def load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    return {}


def save_cache(cache_path: Path, data: dict) -> None:
    cache_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def extract_file(media: MediaFile, cache: dict) -> Extraction:
    """Extract content from a single media file, using cache if available."""
    key = media.path.name

    if key in cache:
        return Extraction(**cache[key])

    if media.is_video:
        transcript = transcribe_video(media.path)
        extraction = Extraction(
            file=key,
            media_type="video",
            transcript=transcript,
            is_educational=bool(transcript and len(transcript) > 20),
        )
    elif media.is_image:
        result = analyze_image(media.path)
        extraction = Extraction(
            file=key,
            media_type="image",
            vision_text=result.get("text", ""),
            vision_description=result.get("description", ""),
            is_educational=result.get("is_educational", False),
        )
    else:
        extraction = Extraction(file=key, media_type="unknown")

    cache[key] = extraction.model_dump()
    return extraction


def extract_all(
    posts: list[list[MediaFile]],
    cache_dir: Path,
    progress: Progress | None = None,
) -> list[list[Extraction]]:
    """Extract content from all posts. Caches results to disk after each file."""
    cache_path = cache_dir / CACHE_FILENAME
    cache = load_cache(cache_path)
    results = []
    task_id = None
    total_files = sum(len(p) for p in posts)

    if progress:
        task_id = progress.add_task("Extracting content", total=total_files)

    for post_files in posts:
        post_extractions = []
        for media in post_files:
            extraction = extract_file(media, cache)
            post_extractions.append(extraction)
            save_cache(cache_path, cache)  # save after each file
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
        results.append(post_extractions)

    return results
```

**Step 4: Run tests**

```bash
pytest tests/test_extractor.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add src/stratalyzer/extractor.py tests/test_extractor.py
git commit -m "feat: extraction pipeline with JSON file caching"
```

---

### Task 6: Post summarization (per-post LLM pass)

**Files:**
- Create: `src/stratalyzer/summarizer.py`
- Create: `tests/test_summarizer.py`

Takes extractions for a single post and produces a PostSummary via Claude.

**Step 1: Write the failing test**

```python
from stratalyzer.summarizer import summarize_post
from stratalyzer.models import Extraction


def test_summarize_post_returns_dict():
    extractions = [
        Extraction(
            file="test_1.jpg",
            media_type="image",
            vision_text="Step 1: Hook them in 3 seconds",
            vision_description="White text on black background, instructional slide",
            is_educational=True,
        ),
        Extraction(
            file="test_2.jpg",
            media_type="image",
            vision_text="Step 2: Deliver value immediately",
            vision_description="White text on black background, instructional slide",
            is_educational=True,
        ),
    ]
    result = summarize_post(
        post_id="12345",
        username="testuser",
        timestamp=1700000000,
        extractions=extractions,
    )
    assert "summary" in result
    assert "topics" in result
    assert isinstance(result["topics"], list)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_summarizer.py -v
```

**Step 3: Implement summarizer**

```python
import json
from anthropic import Anthropic
from stratalyzer.models import Extraction

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


SUMMARIZE_PROMPT = """You are analyzing a single Instagram post from an influencer who teaches courses/strategies.

The post contains {num_files} media files. Here is the extracted content:

{content}

Return a JSON object:
{{
  "summary": "What this post teaches or communicates (2-4 sentences). Be specific about actionable advice, steps, or frameworks shared.",
  "topics": ["topic1", "topic2"],
  "is_educational": true/false
}}

If the post is just a lifestyle photo with no teaching content, set is_educational to false and summarize briefly.
Return ONLY the JSON object."""


def summarize_post(
    post_id: str,
    username: str,
    timestamp: int,
    extractions: list[Extraction],
) -> dict:
    """Summarize a single post's extractions into a structured summary."""
    content_parts = []
    for e in extractions:
        if e.media_type == "video" and e.transcript:
            content_parts.append(f"[Video transcript]: {e.transcript}")
        elif e.media_type == "image":
            if e.vision_text:
                content_parts.append(f"[Image text]: {e.vision_text}")
            if e.vision_description:
                content_parts.append(f"[Image description]: {e.vision_description}")

    content = "\n\n".join(content_parts) if content_parts else "(no extractable content)"

    prompt = SUMMARIZE_PROMPT.format(num_files=len(extractions), content=content)

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)
```

**Step 4: Run tests**

```bash
pytest tests/test_summarizer.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add src/stratalyzer/summarizer.py tests/test_summarizer.py
git commit -m "feat: per-post summarization via Claude"
```

---

### Task 7: Strategy synthesis (final aggregation)

**Files:**
- Create: `src/stratalyzer/synthesizer.py`
- Create: `tests/test_synthesizer.py`

Takes all PostSummaries and produces the final StrategyDocument.

**Step 1: Write the failing test**

```python
from stratalyzer.synthesizer import synthesize_strategy
from stratalyzer.models import PostSummary, Extraction


def test_synthesize_returns_strategy():
    summaries = [
        PostSummary(
            post_id="1",
            username="testuser",
            timestamp=100,
            num_images=2,
            num_videos=0,
            extractions=[],
            summary="Teaches hook-first content strategy for reels",
            topics=["hooks", "reels", "content strategy"],
            is_educational=True,
        ),
        PostSummary(
            post_id="2",
            username="testuser",
            timestamp=200,
            num_images=0,
            num_videos=1,
            extractions=[],
            summary="Explains the 3-second rule for retaining viewers",
            topics=["retention", "reels"],
            is_educational=True,
        ),
    ]
    result = synthesize_strategy("testuser", summaries)
    assert "topics" in result
    assert "processes" in result
    assert "frameworks" in result
```

**Step 2: Run test to verify fails**

```bash
pytest tests/test_synthesizer.py -v
```

**Step 3: Implement synthesizer**

```python
import json
from anthropic import Anthropic
from stratalyzer.models import PostSummary

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


SYNTHESIS_PROMPT = """You are a strategy analyst. Below are summaries of {num_posts} educational Instagram posts from the influencer @{username}.

Your job: synthesize ALL of these into a single structured strategy document. Extract every process, framework, and actionable insight they teach.

POST SUMMARIES:
{summaries}

Return a JSON object with this exact structure:
{{
  "topics": {{
    "Topic Name": ["key point 1", "key point 2", "key point 3"]
  }},
  "processes": [
    {{
      "name": "Process Name",
      "description": "What this process achieves",
      "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
      "source_posts": ["post_id1", "post_id2"]
    }}
  ],
  "frameworks": [
    {{
      "name": "Framework Name",
      "description": "What mental model or conceptual framework they use",
      "components": ["component 1", "component 2"],
      "source_posts": ["post_id1"]
    }}
  ]
}}

Be thorough. Extract EVERY distinct process and framework. Merge duplicates. Be specific — include actual numbers, timeframes, and tactics they mention. This output will be used to build automation software, so precision matters.

Return ONLY the JSON object."""


def synthesize_strategy(username: str, summaries: list[PostSummary]) -> dict:
    """Synthesize all post summaries into a strategy document."""
    # Filter to educational posts only
    edu_summaries = [s for s in summaries if s.is_educational]

    summary_texts = []
    for s in edu_summaries:
        summary_texts.append(
            f"[Post {s.post_id} | Topics: {', '.join(s.topics)}]\n{s.summary}"
        )

    prompt = SYNTHESIS_PROMPT.format(
        num_posts=len(edu_summaries),
        username=username,
        summaries="\n\n".join(summary_texts),
    )

    client = _get_client()
    # Use a larger model for the final synthesis - this is the critical step
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)
```

**Step 4: Run tests**

```bash
pytest tests/test_synthesizer.py -v
```

**Step 5: Commit**

```bash
git add src/stratalyzer/synthesizer.py tests/test_synthesizer.py
git commit -m "feat: strategy synthesis aggregates post summaries into structured output"
```

---

### Task 8: Wire up CLI with full pipeline

**Files:**
- Modify: `src/stratalyzer/cli.py`

**Step 1: Implement the full `analyze` command**

```python
import json
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress
from stratalyzer.scanner import scan_folder
from stratalyzer.extractor import extract_all
from stratalyzer.summarizer import summarize_post
from stratalyzer.synthesizer import synthesize_strategy
from stratalyzer.models import PostSummary, StrategyDocument, Extraction

console = Console()


@click.group()
def main():
    """Stratalyzer - Extract strategies from influencer content."""
    pass


@main.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", default=None, help="Output JSON file path")
@click.option("--skip-synthesis", is_flag=True, help="Only extract, don't synthesize")
def analyze(folder: str, output: str | None, skip_synthesis: bool):
    """Analyze a folder of influencer content."""
    folder_path = Path(folder)

    # Step 1: Scan
    console.print(f"[bold]Scanning {folder_path.name}...[/bold]")
    posts = scan_folder(folder_path)
    total_files = sum(len(p) for p in posts)
    console.print(f"Found {len(posts)} posts ({total_files} files)")

    # Step 2: Extract
    console.print("[bold]Extracting content...[/bold]")
    with Progress() as progress:
        all_extractions = extract_all(posts, folder_path, progress)

    # Step 3: Summarize each post
    console.print("[bold]Summarizing posts...[/bold]")
    summaries: list[PostSummary] = []
    username = posts[0][0].username if posts else "unknown"

    with Progress() as progress:
        task = progress.add_task("Summarizing", total=len(posts))
        for post_files, extractions in zip(posts, all_extractions):
            first = post_files[0]
            result = summarize_post(
                post_id=first.post_id,
                username=first.username,
                timestamp=first.timestamp,
                extractions=extractions,
            )
            summary = PostSummary(
                post_id=first.post_id,
                username=first.username,
                timestamp=first.timestamp,
                num_images=sum(1 for f in post_files if f.is_image),
                num_videos=sum(1 for f in post_files if f.is_video),
                extractions=[e.model_dump() for e in extractions],
                summary=result["summary"],
                topics=result.get("topics", []),
                is_educational=result.get("is_educational", False),
            )
            summaries.append(summary)
            progress.update(task, advance=1)

    edu_count = sum(1 for s in summaries if s.is_educational)
    console.print(f"[green]{edu_count}/{len(summaries)} posts are educational[/green]")

    if skip_synthesis:
        # Just dump summaries
        out_path = Path(output) if output else folder_path / "summaries.json"
        out_path.write_text(
            json.dumps([s.model_dump() for s in summaries], indent=2, default=str),
            encoding="utf-8",
        )
        console.print(f"[bold green]Summaries saved to {out_path}[/bold green]")
        return

    # Step 4: Synthesize
    console.print("[bold]Synthesizing strategy document...[/bold]")
    strategy = synthesize_strategy(username, summaries)

    # Build final document
    doc = StrategyDocument(
        influencer=username,
        total_posts=len(summaries),
        educational_posts=edu_count,
        topics=strategy.get("topics", {}),
        processes=strategy.get("processes", []),
        frameworks=strategy.get("frameworks", []),
        raw_post_summaries=summaries,
    )

    out_path = Path(output) if output else folder_path / "strategy.json"
    out_path.write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Strategy document saved to {out_path}[/bold green]")
    console.print(f"  Topics: {len(doc.topics)}")
    console.print(f"  Processes: {len(doc.processes)}")
    console.print(f"  Frameworks: {len(doc.frameworks)}")
```

**Step 2: Test the full pipeline on a small subset**

```bash
# Quick smoke test: run on just a few files manually, or the full folder
cd C:/Users/asus/Desktop/projects/stratalyzer
stratalyzer analyze iamchrischung/
```

**Step 3: Commit**

```bash
git add src/stratalyzer/cli.py
git commit -m "feat: wire up full analysis pipeline in CLI"
```

---

### Task 9: Summaries caching (avoid re-summarizing)

**Files:**
- Modify: `src/stratalyzer/cli.py`

The extraction cache (Task 5) caches raw file extractions. This task adds a second cache layer for post summaries, so if you re-run the tool after extraction is complete, it doesn't re-call Claude for every post summary.

**Step 1: Add summary cache logic to cli.py**

In the summarization loop, check for `{folder}/.stratalyzer_summaries.json`. Load it, skip posts that already have summaries, save after each new summary.

```python
# Add to analyze() before the summarize loop:
summary_cache_path = folder_path / ".stratalyzer_summaries.json"
summary_cache = {}
if summary_cache_path.exists():
    summary_cache = json.loads(summary_cache_path.read_text(encoding="utf-8"))

# In the loop, wrap the summarize_post call:
if first.post_id in summary_cache:
    result = summary_cache[first.post_id]
else:
    result = summarize_post(...)
    summary_cache[first.post_id] = result
    summary_cache_path.write_text(json.dumps(summary_cache, indent=2, default=str), encoding="utf-8")
```

**Step 2: Test by running analyze twice - second run should be fast**

```bash
stratalyzer analyze iamchrischung/
# Run again - should skip extraction and summarization
stratalyzer analyze iamchrischung/
```

**Step 3: Commit**

```bash
git add src/stratalyzer/cli.py
git commit -m "feat: add summary caching to avoid re-calling Claude on reruns"
```

---

## Execution Notes

- **Total API cost estimate**: ~332 Sonnet vision calls for images ($0.003/image ~= $1) + ~78 local Whisper transcriptions (free) + ~N summarization calls + 1 synthesis call. Roughly $2-5 total.
- **Whisper model**: `base` is fast and good enough for clear speech. Upgrade to `medium` if transcripts are poor.
- **Rate limits**: The extraction loop processes one file at a time sequentially. If Anthropic rate limits hit, add a simple `time.sleep(0.5)` between vision calls.
- **The pipeline is resumable**: cache files in the content folder mean you can ctrl+c and restart without losing progress.
