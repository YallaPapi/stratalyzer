import json
from unittest.mock import patch, MagicMock
from stratalyzer.method_merger import deduplicate_methods
from stratalyzer.models import MethodSpec, MethodStep


def _mock_grok_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def test_dedup_groups_same_methods():
    specs = [
        MethodSpec(
            post_id="p1", has_method=True,
            method_name="Silent Film Storytelling Method",
            method_type="production_technique",
            detailed_explanation="Version 1 explanation with 5 steps...",
            step_by_step=[MethodStep(step=1, action="Start with pain", detail="Pain hooks viewers")],
            rules=["Keep text in same position"],
            related_topics=["video editing"],
        ),
        MethodSpec(
            post_id="p2", has_method=True,
            method_name="Silent Film Storytelling",
            method_type="production_technique",
            detailed_explanation="Version 2 with view milestones...",
            step_by_step=[MethodStep(step=1, action="Hook with struggle", detail="Opens with struggle text")],
            rules=["Use rising action audio"],
            creator_results="24.5M views on pinned reel",
            related_topics=["retention"],
        ),
        MethodSpec(
            post_id="p3", has_method=True,
            method_name="Lego Method",
            method_type="ideation_system",
            detailed_explanation="Content ideation using building blocks...",
            step_by_step=[MethodStep(step=1, action="Find your message", detail="Ask what friends come to you for")],
            related_topics=["content ideas"],
        ),
    ]

    grouping_response = json.dumps({
        "groups": [
            {"method_name": "Silent Film Storytelling Method", "post_ids": ["p1", "p2"]},
            {"method_name": "Lego Method", "post_ids": ["p3"]},
        ]
    })

    merged_response = json.dumps({
        "method_name": "Silent Film Storytelling Method",
        "method_type": "production_technique",
        "detailed_explanation": "Combined explanation from both videos...",
        "specific_examples": ["24.5M views on pinned reel"],
        "inputs": "Raw footage + transformation story",
        "outputs": "Muted-optimized video",
        "step_by_step": [
            {"step": 1, "action": "Start with pain", "detail": "Combined detail from both", "visual_reference": None}
        ],
        "rules": ["Keep text in same position", "Use rising action audio"],
        "creator_results": "24.5M views on pinned reel",
        "related_topics": ["video editing", "retention"],
    })

    with patch("stratalyzer.method_merger._get_client") as mock_client:
        mock = mock_client.return_value.chat.completions.create
        mock.side_effect = [
            _mock_grok_response(grouping_response),
            _mock_grok_response(merged_response),
        ]
        results = deduplicate_methods(specs)

    assert len(results) == 2
    names = {r.method_name for r in results}
    assert "Silent Film Storytelling Method" in names
    assert "Lego Method" in names

    silent = [r for r in results if r.method_name == "Silent Film Storytelling Method"][0]
    assert set(silent.source_posts) == {"p1", "p2"}


def test_dedup_empty_list():
    results = deduplicate_methods([])
    assert results == []


def test_dedup_skips_non_methods():
    specs = [
        MethodSpec(post_id="p1", has_method=False, skip_reason="Music video"),
    ]
    results = deduplicate_methods(specs)
    assert results == []
