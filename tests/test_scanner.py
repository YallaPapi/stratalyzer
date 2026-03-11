import tempfile
from pathlib import Path
from stratalyzer.scanner import scan_folder


def test_scan_groups_by_post():
    with tempfile.TemporaryDirectory() as d:
        # Two files from same post (same post_id)
        Path(d, "user_100_999_123_1.jpg").touch()
        Path(d, "user_100_999_123_2.jpg").touch()
        # One file from different post
        Path(d, "user_200_888_123_1.mp4").touch()
        # Non-media file should be ignored
        Path(d, "readme.txt").touch()

        posts = scan_folder(d)
        assert len(posts) == 2
        post_999 = next(p for p in posts if p[0].post_id == "999")
        assert len(post_999) == 2
        # Files should be sorted by index
        assert post_999[0].index == 1
        assert post_999[1].index == 2


def test_scan_empty_folder():
    with tempfile.TemporaryDirectory() as d:
        posts = scan_folder(d)
        assert len(posts) == 0
