import json
from anthropic import Anthropic
from stratalyzer.models import PostSummary

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


SYNTHESIS_PROMPT = """You are a strategy analyst. Below are summaries of {num_posts} educational Instagram posts from the influencer @{username}.

Your job: synthesize ALL of these into a single structured strategy document. Extract every process, framework, and actionable insight they teach.

POST SUMMARIES:
{summaries}

Return a JSON object with this exact structure:
{{
  "topics": {{
    "Topic Name": ["key point 1", "key point 2", "key point 3"]
  }},
  "processes": [
    {{
      "name": "Process Name",
      "description": "What this process achieves",
      "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
      "source_posts": ["post_id1", "post_id2"]
    }}
  ],
  "frameworks": [
    {{
      "name": "Framework Name",
      "description": "What mental model or conceptual framework they use",
      "components": ["component 1", "component 2"],
      "source_posts": ["post_id1"]
    }}
  ]
}}

Be thorough. Extract EVERY distinct process and framework. Merge duplicates. Be specific — include actual numbers, timeframes, and tactics they mention. This output will be used to build automation software, so precision matters.

Return ONLY the JSON object."""


def synthesize_strategy(username: str, summaries: list[PostSummary]) -> dict:
    """Synthesize all post summaries into a strategy document."""
    # Include ALL posts that have any content, not just "educational" ones
    content_summaries = [s for s in summaries if s.summary and s.summary != "(no extractable content)"]

    summary_texts = []
    for s in content_summaries:
        summary_texts.append(
            f"[Post {s.post_id} | Topics: {', '.join(s.topics)}]\n{s.summary}"
        )

    prompt = SYNTHESIS_PROMPT.format(
        num_posts=len(content_summaries),
        username=username,
        summaries="\n\n".join(summary_texts),
    )

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16384,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)
