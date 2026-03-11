from pathlib import Path
from stratalyzer.vision import analyze_image

TEST_IMAGE = Path("iamchrischung/iamchrischung_1762530570_3760701455611845401_17814358_7.jpg")


def test_analyze_image_returns_extraction():
    if not TEST_IMAGE.exists():
        import pytest
        pytest.skip("Test image not available")
    result = analyze_image(TEST_IMAGE)
    assert "text" in result
    assert "description" in result
    assert "is_educational" in result
    assert isinstance(result["is_educational"], bool)
