from stratalyzer.synthesizer import synthesize_strategy
from stratalyzer.models import PostSummary


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
