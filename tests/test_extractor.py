import json
import tempfile
from pathlib import Path
from stratalyzer.extractor import load_cache, save_cache


def test_cache_round_trip():
    with tempfile.TemporaryDirectory() as d:
        cache_path = Path(d) / "cache.json"
        save_cache(cache_path, {"file1.jpg": {"text": "hello"}})
        data = load_cache(cache_path)
        assert data["file1.jpg"]["text"] == "hello"


def test_cache_missing_file():
    data = load_cache(Path("/nonexistent/cache.json"))
    assert data == {}
