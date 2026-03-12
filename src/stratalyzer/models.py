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
        import re
        stem = path.stem

        # Format 2: @username-YYYY-MM-DD_HHMM-title-slug-postid.ext
        # e.g. @lacedmedia-2023-04-14_0216-Simple-tip-...-7221615387643776299
        m = re.match(
            r"@([^-]+)-(\d{4}-\d{2}-\d{2}_\d{4})-.*?-(\d{10,})$", stem
        )
        if m:
            username = m.group(1)
            date_str = m.group(2)  # "2023-04-14_0216"
            post_id = m.group(3)
            # Convert date to a sortable int timestamp (YYYYMMDDHHNN)
            clean = date_str.replace("-", "").replace("_", "")
            timestamp = int(clean)
            return cls(
                path=path,
                username=username,
                timestamp=timestamp,
                post_id=post_id,
                user_id="0",
                index=0,
                ext=path.suffix.lstrip(".").lower(),
            )

        # Format 1: username_timestamp_postid_userid_index.ext
        # e.g. iamchrischung_1234567890_abc123_12345_0
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


class MethodStep(BaseModel):
    """One step in a method's step-by-step breakdown."""
    step: int
    action: str
    detail: str
    visual_reference: str | None = None


class MethodSpec(BaseModel):
    """Deep analysis output for a single video's method/teaching."""
    post_id: str
    has_method: bool
    method_name: str | None = None
    method_type: str | None = None
    detailed_explanation: str | None = None
    specific_examples: list[str] = []
    inputs: str | None = None
    outputs: str | None = None
    step_by_step: list[MethodStep] = []
    rules: list[str] = []
    creator_results: str | None = None
    related_topics: list[str] = []
    skip_reason: str | None = None
    source_posts: list[str] = []
