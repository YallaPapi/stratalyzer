import json
from unittest.mock import patch, MagicMock
from stratalyzer.method_analyzer import analyze_single_video
from stratalyzer.models import Extraction, MethodSpec


def _mock_grok_response(content: str):
    """Create a mock OpenAI chat completion response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def test_analyze_educational_video():
    extraction = Extraction(
        file="test_video.mp4",
        media_type="video",
        transcript="Here are five steps to write better hooks. Step one, lead with pain...",
        vision_text="5 HOOK WRITING TIPS",
        vision_description="Creator at desk explaining hook writing with text overlays showing each step",
        is_educational=True,
    )

    fake_response = json.dumps({
        "has_method": True,
        "method_name": "5-Step Hook Writing Process",
        "method_type": "writing_technique",
        "detailed_explanation": "A complete process for writing hooks that...",
        "specific_examples": ["Lead with pain example"],
        "inputs": "A topic to write a hook for",
        "outputs": "A polished hook following the 5-step process",
        "step_by_step": [
            {"step": 1, "action": "Lead with pain", "detail": "Start with the audience's struggle", "visual_reference": None}
        ],
        "rules": ["Always use second person"],
        "creator_results": "Creator claims this is their top method",
        "related_topics": ["hooks", "copywriting"],
    })

    with patch("stratalyzer.method_analyzer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = _mock_grok_response(fake_response)
        result = analyze_single_video("post123", extraction)

    assert isinstance(result, MethodSpec)
    assert result.has_method is True
    assert result.method_name == "5-Step Hook Writing Process"
    assert len(result.step_by_step) == 1
    assert result.post_id == "post123"


def test_analyze_non_educational_video():
    extraction = Extraction(
        file="test_video.mp4",
        media_type="video",
        transcript="Music",
        vision_description="Person dancing",
        is_educational=False,
    )

    fake_response = json.dumps({
        "has_method": False,
        "skip_reason": "Music/dance video with no teaching content",
    })

    with patch("stratalyzer.method_analyzer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = _mock_grok_response(fake_response)
        result = analyze_single_video("post456", extraction)

    assert result.has_method is False
    assert result.skip_reason is not None
    assert result.post_id == "post456"
