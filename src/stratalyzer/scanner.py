from pathlib import Path
from collections import defaultdict
from stratalyzer.models import MediaFile

MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm"}


def scan_folder(folder: str | Path) -> list[list[MediaFile]]:
    """Scan folder, return files grouped by post_id, sorted by index."""
    folder = Path(folder)
    groups: dict[int, list[MediaFile]] = defaultdict(list)

    for f in folder.iterdir():
        if not f.is_file() or f.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        try:
            media = MediaFile.from_filename(f)
            groups[media.timestamp].append(media)
        except (ValueError, IndexError):
            continue

    result = []
    for timestamp, files in groups.items():
        files.sort(key=lambda m: m.index)
        result.append(files)

    result.sort(key=lambda g: g[0].timestamp)
    return result
