import json
from pathlib import Path
from rich.progress import Progress
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
            save_cache(cache_path, cache)
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
        results.append(post_extractions)

    return results
