import json
from anthropic import Anthropic
from stratalyzer.models import Extraction

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


SUMMARIZE_PROMPT = """You are analyzing a single Instagram post from an influencer who teaches courses/strategies.

The post contains {num_files} media files. Here is the extracted content:

{content}

Return a JSON object:
{{
  "summary": "What this post teaches or communicates (2-4 sentences). Be specific about actionable advice, steps, or frameworks shared.",
  "topics": ["topic1", "topic2"],
  "is_educational": true/false
}}

If the post is just a lifestyle photo with no teaching content, set is_educational to false and summarize briefly.
Return ONLY the JSON object."""


def summarize_post(
    post_id: str,
    username: str,
    timestamp: int,
    extractions: list[Extraction],
) -> dict:
    """Summarize a single post's extractions into a structured summary."""
    content_parts = []
    for e in extractions:
        if e.media_type == "video" and e.transcript:
            content_parts.append(f"[Video transcript]: {e.transcript}")
        elif e.media_type == "image":
            if e.vision_text:
                content_parts.append(f"[Image text]: {e.vision_text}")
            if e.vision_description:
                content_parts.append(f"[Image description]: {e.vision_description}")

    content = "\n\n".join(content_parts) if content_parts else "(no extractable content)"

    prompt = SUMMARIZE_PROMPT.format(num_files=len(extractions), content=content)

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)
