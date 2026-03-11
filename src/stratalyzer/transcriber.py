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


def transcribe_video(video_path: Path) -> str:
    """Transcribe a video file using Whisper. Returns transcript text."""
    model = _get_model()
    result = model.transcribe(str(video_path), language="en")
    return result["text"].strip()
