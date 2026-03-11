import base64
import json
from pathlib import Path
from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


VISION_PROMPT = """Analyze this Instagram post image. Return a JSON object with exactly these fields:

{
  "text": "all text visible in the image, transcribed exactly",
  "description": "brief description of what the image shows (1-2 sentences)",
  "is_educational": true/false (does this image teach something, share a framework, give advice, or contain instructional text?)
}

If there is no visible text, set "text" to "".
Return ONLY the JSON object, no other text."""


def analyze_image(image_path: Path) -> dict:
    """Analyze an image using Claude Vision. Returns dict with text, description, is_educational."""
    client = _get_client()
    data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    suffix = image_path.suffix.lower().lstrip(".")
    media_type = f"image/{'jpeg' if suffix in ('jpg', 'jpeg') else suffix}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)
