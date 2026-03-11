import tempfile
from pathlib import Path
from stratalyzer.scanner import scan_folder


def test_scan_groups_by_post():
    with tempfile.TemporaryDirectory() as d:
        # Two files from same post (same timestamp)
        Path(d, "user_100_999_123_1.jpg").touch()
        Path(d, "user_100_888_123_2.jpg").touch()
        # One file from different post (different timestamp)
        Path(d, "user_200_777_123_1.mp4").touch()
        # Non-media file should be ignored
        Path(d, "readme.txt").touch()

        posts = scan_folder(d)
        assert len(posts) == 2
        post_100 = next(p for p in posts if p[0].timestamp == 100)
        assert len(post_100) == 2
        # Files should be sorted by index
        assert post_100[0].index == 1
        assert post_100[1].index == 2


def test_scan_empty_folder():
    with tempfile.TemporaryDirectory() as d:
        posts = scan_folder(d)
        assert len(posts) == 0
