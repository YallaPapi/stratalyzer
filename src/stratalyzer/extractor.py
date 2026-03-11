import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from rich.progress import Progress
from stratalyzer.models import MediaFile, Extraction
from stratalyzer.transcriber import transcribe_video
from stratalyzer.vision import analyze_image

CACHE_FILENAME = ".stratalyzer_cache.json"
MAX_VISION_WORKERS = 10
MAX_WHISPER_WORKERS = 1  # Whisper/PyTorch not thread-safe

_cache_lock = threading.Lock()


def load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    return {}


def save_cache(cache_path: Path, data: dict) -> None:
    cache_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _extract_single(media: MediaFile, cache: dict, cache_path: Path) -> Extraction:
    """Extract content from a single media file, using cache if available."""
    key = media.path.name

    with _cache_lock:
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

    with _cache_lock:
        cache[key] = extraction.model_dump()
        save_cache(cache_path, cache)

    return extraction


def extract_all(
    posts: list[list[MediaFile]],
    cache_dir: Path,
    progress: Progress | None = None,
) -> list[list[Extraction]]:
    """Extract content from all posts with parallel processing."""
    cache_path = cache_dir / CACHE_FILENAME
    cache = load_cache(cache_path)

    # Flatten all files, remembering which post they belong to
    all_media: list[MediaFile] = []
    post_indices: list[int] = []  # maps flat index -> post index
    for i, post_files in enumerate(posts):
        for media in post_files:
            all_media.append(media)
            post_indices.append(i)

    total_files = len(all_media)
    task_id = None
    if progress:
        task_id = progress.add_task("Extracting content", total=total_files)

    # Split into images (I/O-bound, high parallelism) and videos (CPU-bound, low parallelism)
    image_items = [(idx, m) for idx, m in enumerate(all_media) if m.is_image]
    video_items = [(idx, m) for idx, m in enumerate(all_media) if m.is_video]
    other_items = [(idx, m) for idx, m in enumerate(all_media) if not m.is_image and not m.is_video]

    extractions_by_idx: dict[int, Extraction] = {}

    def _do_extract(idx_media):
        idx, media = idx_media
        return idx, _extract_single(media, cache, cache_path)

    # Process images in parallel (API calls, I/O-bound)
    with ThreadPoolExecutor(max_workers=MAX_VISION_WORKERS) as executor:
        futures = {executor.submit(_do_extract, item): item for item in image_items}
        for future in as_completed(futures):
            try:
                idx, extraction = future.result()
                extractions_by_idx[idx] = extraction
            except Exception as e:
                flat_idx, media = futures[future]
                extractions_by_idx[flat_idx] = Extraction(
                    file=media.path.name, media_type="image",
                    vision_description=f"Error: {e}", is_educational=False,
                )
            if progress and task_id is not None:
                progress.update(task_id, advance=1)

    # Process videos sequentially (Whisper/PyTorch not thread-safe)
    for idx, media in video_items:
        try:
            extraction = _extract_single(media, cache, cache_path)
        except Exception as e:
            extraction = Extraction(
                file=media.path.name, media_type="video",
                transcript=f"Error: {e}", is_educational=False,
            )
        extractions_by_idx[idx] = extraction
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    # Process any other files
    for idx, media in other_items:
        extraction = _extract_single(media, cache, cache_path)
        extractions_by_idx[idx] = extraction
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    # Reassemble into post groups
    results: list[list[Extraction]] = [[] for _ in posts]
    for flat_idx in range(total_files):
        post_idx = post_indices[flat_idx]
        results[post_idx].append(extractions_by_idx[flat_idx])

    return results
