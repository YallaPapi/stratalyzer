"""Mine YouTube channel transcripts for viral-quality takes."""
import json
import re
from pathlib import Path
from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def parse_vtt(vtt_path: Path) -> str:
    """Parse a .vtt subtitle file into clean text, removing timestamps and deduplicating."""
    raw = vtt_path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()

    # Skip header lines (WEBVTT, Kind:, Language:, etc.)
    text_lines = []
    seen = set()
    for line in lines:
        line = line.strip()
        # Skip empty, header, timestamp lines
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->", line):
            continue
        if re.match(r"^<\d{2}:\d{2}:\d{2}\.\d{3}>", line):
            continue
        if line.startswith("NOTE"):
            continue
        # Strip VTT tags like <c>, </c>, <00:00:00.000>
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if not clean:
            continue
        # Deduplicate (YouTube VTT repeats lines across cue boundaries)
        if clean not in seen:
            seen.add(clean)
            text_lines.append(clean)

    return " ".join(text_lines)


def parse_all_transcripts(transcript_dir: Path) -> dict[str, dict]:
    """Parse all .vtt files in a directory into {filename: {text, word_count}}."""
    results = {}
    vtt_files = sorted(transcript_dir.glob("*.vtt"))
    for vtt in vtt_files:
        text = parse_vtt(vtt)
        word_count = len(text.split())
        # Use the video title (strip .en.vtt suffix)
        title = vtt.stem
        for suffix in [".en", ".en-orig"]:
            if title.endswith(suffix):
                title = title[: -len(suffix)]
                break
        results[title] = {
            "file": vtt.name,
            "text": text,
            "word_count": word_count,
        }
    return results


SCORE_PROMPT = """You are a viral content scout. You are reading a LONG video transcript (likely 15-60 minutes) \
and your job is to find EVERY segment that could become a standalone viral short-form video.

A segment is viral-quality if it scores high on ALL THREE of these:

1. **SKIN IN THE GAME** — The speaker has personal experience, real stakes, or insider knowledge. \
They actually DID the thing, lost the money, made the mistake. A personal war story = 9-10. \
Generic advice with no personal stake = 1-3.

2. **REFRAME POTENTIAL** — There's a non-obvious take. A familiar truth restated in a way that flips \
the viewer's assumption. "Just work hard" = 1. "Perfectionism is fear wearing a productivity costume" = 9.

3. **EMOTIONAL PUNCH** — Reading the distilled version would make someone feel something in their chest. \
"Here are 5 tips" = 1. "People dumber than you are making more money because they're actually doing it" = 9.

For EACH segment you find (find as many as exist, could be 1 could be 15):
- Extract the relevant portion of transcript (the actual words)
- Score it on all three criteria
- Write a draft "take" — the non-obvious reframe that could be the caption/hook
- Approximate where in the transcript it occurs (early/middle/late or rough word position)

IMPORTANT: Scan the ENTIRE transcript. Don't stop after finding 3. Long videos often have \
10+ usable segments scattered throughout. Find ALL of them.

TRANSCRIPT:
{transcript}

Return a JSON object:
{{
  "video_summary": "what this video is about in one sentence",
  "total_segments_found": <number>,
  "segments": [
    {{
      "segment_topic": "what this segment is about",
      "skin_in_the_game": <1-10>,
      "reframe_potential": <1-10>,
      "emotional_punch": <1-10>,
      "overall_score": <1-10>,
      "draft_take": "the non-obvious reframe / viral hook for this segment",
      "source_quote": "the key lines from the transcript (50-150 words)",
      "position": "early/middle/late"
    }}
  ]
}}

Return ONLY valid JSON, no other text."""


def score_transcript(transcript: str) -> dict:
    """Score a transcript for viral potential. Finds multiple segments in long transcripts."""
    # For very long transcripts, we still need to fit in context window
    # but we send more than before — 8000 words covers ~30 min of speech
    words = transcript.split()
    if len(words) > 8000:
        transcript = " ".join(words[:8000])

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": SCORE_PROMPT.format(transcript=transcript)}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def score_all(
    transcripts: dict[str, dict],
    min_words: int = 100,
    output_path: Path | None = None,
    on_progress=None,
) -> list[dict]:
    """Score all transcripts for viral potential.

    Returns a flat list of individual segments/takes sorted by score (best first).
    Long videos will produce multiple segments each.
    """
    eligible = {k: v for k, v in transcripts.items() if v["word_count"] >= min_words}

    all_segments = []
    video_results = []
    total = len(eligible)
    done = 0

    for title, data in eligible.items():
        done += 1
        if on_progress:
            on_progress(f"[{done}/{total}] Scanning: {title[:60]}...")

        try:
            result = score_transcript(data["text"])
            segments = result.get("segments", [])
            video_summary = result.get("video_summary", "")

            # Flatten: each segment becomes its own entry with video metadata
            for seg in segments:
                seg["video_title"] = title
                seg["video_file"] = data["file"]
                seg["video_word_count"] = data["word_count"]
                seg["video_summary"] = video_summary
                all_segments.append(seg)

            video_results.append({
                "title": title,
                "file": data["file"],
                "word_count": data["word_count"],
                "video_summary": video_summary,
                "segments_found": len(segments),
            })

            if on_progress:
                on_progress(f"  Found {len(segments)} segments")

        except Exception as e:
            if on_progress:
                on_progress(f"  ERROR: {e}")
            video_results.append({
                "title": title,
                "file": data["file"],
                "word_count": data["word_count"],
                "segments_found": 0,
                "error": str(e),
            })

        # Save incrementally
        if output_path:
            all_segments.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
            save_data = {
                "total_videos_scanned": done,
                "total_segments_found": len(all_segments),
                "segments": all_segments,
                "video_summary": video_results,
            }
            output_path.write_text(
                json.dumps(save_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    all_segments.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    return all_segments
