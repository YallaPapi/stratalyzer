import subprocess
import tempfile
from pathlib import Path
import whisper

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


def _has_audio(video_path: Path) -> bool:
    """Check if video file contains an audio stream."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0",
             str(video_path)],
            capture_output=True, text=True, timeout=10,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def transcribe_video(video_path: Path) -> str:
    """Transcribe a video file using Whisper. Returns transcript text."""
    try:
        model = _get_model()
        result = model.transcribe(str(video_path), language="en")
        return result["text"].strip()
    except Exception:
        return ""
