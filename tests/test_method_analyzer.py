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


def test_analyze_all_caches_results(tmp_path):
    from stratalyzer.method_analyzer import analyze_all_videos
    from stratalyzer.models import PostSummary

    summaries = [
        PostSummary(
            post_id="post1", username="test", timestamp=202501010000,
            num_images=0, num_videos=1,
            extractions=[Extraction(
                file="v1.mp4", media_type="video",
                transcript="Here are 3 steps to grow...",
                vision_description="Creator at desk explaining growth",
                is_educational=True,
            )],
            summary="Teaches growth", topics=["growth"], is_educational=True,
        ),
    ]

    fake_response = json.dumps({
        "has_method": True,
        "method_name": "3-Step Growth Method",
        "method_type": "growth_tactic",
        "detailed_explanation": "Full explanation...",
        "specific_examples": [],
        "inputs": "An account to grow",
        "outputs": "A growth plan",
        "step_by_step": [{"step": 1, "action": "Do this", "detail": "Like this", "visual_reference": None}],
        "rules": [],
        "creator_results": "10K followers in 30 days",
        "related_topics": ["growth"],
    })

    with patch("stratalyzer.method_analyzer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = _mock_grok_response(fake_response)
        results = analyze_all_videos(summaries, cache_dir=tmp_path)

    assert len(results) == 1
    assert results[0].method_name == "3-Step Growth Method"

    # Verify cache was written
    cache_file = tmp_path / ".stratalyzer_methods_cache.json"
    assert cache_file.exists()
    cached = json.loads(cache_file.read_text())
    assert "post1" in cached

    # Second call should use cache, not API
    with patch("stratalyzer.method_analyzer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.side_effect = Exception("Should not be called")
        results2 = analyze_all_videos(summaries, cache_dir=tmp_path)

    assert len(results2) == 1
    assert results2[0].method_name == "3-Step Growth Method"
