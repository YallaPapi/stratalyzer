from pathlib import Path
from stratalyzer.transcriber import transcribe_video

TEST_VIDEO = Path("iamchrischung/iamchrischung_1772628983_3845412592060005965_17814358_1.mp4")


def test_transcribe_returns_string():
    if not TEST_VIDEO.exists():
        import pytest
        pytest.skip("Test video not available")
    result = transcribe_video(TEST_VIDEO)
    assert isinstance(result, str)
