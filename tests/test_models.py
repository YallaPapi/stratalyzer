from pathlib import Path
from stratalyzer.models import MediaFile


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
