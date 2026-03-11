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
