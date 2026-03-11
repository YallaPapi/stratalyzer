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
    file: str
    media_type: str
    transcript: str | None = None
    vision_text: str | None = None
    vision_description: str | None = None
    is_educational: bool = False


class PostSummary(BaseModel):
    """Aggregated content from one Instagram post."""
    post_id: str
    username: str
    timestamp: int
    num_images: int
    num_videos: int
    extractions: list[Extraction]
    summary: str
    topics: list[str]
    is_educational: bool


class Process(BaseModel):
    """A step-by-step process the influencer teaches."""
    name: str
    description: str
    steps: list[str]
    source_posts: list[str]


class Framework(BaseModel):
    """A conceptual framework or mental model the influencer uses."""
    name: str
    description: str
    components: list[str]
    source_posts: list[str]


class StrategyDocument(BaseModel):
    """Final synthesized output - the machine-readable strategy."""
    influencer: str
    total_posts: int
    educational_posts: int
    topics: dict[str, list[str]]
    processes: list[Process]
    frameworks: list[Framework]
    raw_post_summaries: list[PostSummary]
