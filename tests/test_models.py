from pathlib import Path
from stratalyzer.models import MediaFile, MethodSpec, MethodStep


def test_parse_filename_jpg():
    p = Path("iamchrischung_1762530570_3760701455611845401_17814358_7.jpg")
    m = MediaFile.from_filename(p)
    assert m.username == "iamchrischung"
    assert m.timestamp == 1762530570
    assert m.post_id == "3760701455611845401"
    assert m.user_id == "17814358"
    assert m.index == 7
    assert m.ext == "jpg"
    assert m.is_image
    assert not m.is_video


def test_parse_filename_mp4():
    p = Path("iamchrischung_1772628983_3845412592060005965_17814358_1.mp4")
    m = MediaFile.from_filename(p)
    assert m.username == "iamchrischung"
    assert m.timestamp == 1772628983
    assert m.ext == "mp4"
    assert m.is_video
    assert not m.is_image


def test_method_spec_creation():
    step = MethodStep(
        step=1,
        action="Open with pain/struggle frames",
        detail="The pain is what people connect to",
        visual_reference="Creator shows distress in opening frames",
    )
    spec = MethodSpec(
        post_id="123",
        has_method=True,
        method_name="Silent Film Method",
        method_type="production_technique",
        detailed_explanation="Full explanation here...",
        specific_examples=["24.5M views on pinned reel"],
        inputs="Raw video footage + transformation story",
        outputs="Short-form video optimized for muted viewing",
        step_by_step=[step],
        rules=["All text same position across frames"],
        creator_results="24.5M views on pinned reel",
        related_topics=["video editing", "retention"],
    )
    assert spec.method_name == "Silent Film Method"
    assert len(spec.step_by_step) == 1
    assert spec.step_by_step[0].action == "Open with pain/struggle frames"


def test_method_spec_no_method():
    spec = MethodSpec(
        post_id="456",
        has_method=False,
        skip_reason="Music-only video",
    )
    assert spec.has_method is False
    assert spec.method_name is None
