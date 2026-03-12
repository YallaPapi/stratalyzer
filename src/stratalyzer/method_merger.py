"""Deduplicate and merge MethodSpecs that teach the same method."""

import json
import os
from openai import OpenAI
from stratalyzer.models import MethodSpec

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("XAI_API_KEY", "")
        _client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    return _client


GROUPING_PROMPT = """Below is a list of methods extracted from a content creator's videos. Some of these are the SAME method taught in different videos. Group them.

METHODS:
{methods_list}

Return a JSON object:
{{
  "groups": [
    {{
      "method_name": "the canonical name for this method",
      "post_ids": ["id1", "id2"]
    }}
  ]
}}

Rules:
- If two methods teach the same thing with slightly different names (e.g. "Silent Film Storytelling Method" and "Silent Film Storytelling"), they are the SAME method.
- If two methods are genuinely different techniques, they are SEPARATE groups even if they share a topic.
- A method that appears in only one video is still its own group with one post_id.

Return ONLY the JSON object."""


MERGE_PROMPT = """Below are multiple detailed specifications of the SAME method, extracted from different videos by the same creator. Merge them into one comprehensive specification that preserves ALL detail from ALL sources. Nothing gets lost — if one version has an example the other doesn't, include both.

SPECIFICATIONS:
{specs_json}

Return a JSON object with this structure:
{{
  "method_name": "canonical name",
  "method_type": "type",
  "detailed_explanation": "merged comprehensive explanation preserving all detail from all sources",
  "specific_examples": ["all examples from all sources"],
  "inputs": "what's needed to start",
  "outputs": "what gets produced",
  "step_by_step": [
    {{"step": 1, "action": "what", "detail": "how — merged from all sources", "visual_reference": "merged"}}
  ],
  "rules": ["all rules from all sources, deduplicated"],
  "creator_results": "all results/proof mentioned across all sources",
  "related_topics": ["merged tags"]
}}

Return ONLY the JSON object."""


def deduplicate_methods(specs: list[MethodSpec]) -> list[MethodSpec]:
    """Group duplicate methods and merge their specs."""
    # Filter to only specs that have methods
    method_specs = [s for s in specs if s.has_method]

    if not method_specs:
        return []

    client = _get_client()

    # Step 1: Ask Grok to group by method similarity
    methods_list = "\n".join(
        f"- post_id={s.post_id}: \"{s.method_name}\" ({s.method_type}) — {(s.detailed_explanation or '')[:200]}"
        for s in method_specs
    )

    response = client.chat.completions.create(
        model="grok-4-1-fast-non-reasoning",
        max_tokens=8192,
        messages=[{"role": "user", "content": GROUPING_PROMPT.format(methods_list=methods_list)}],
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    grouping = json.loads(text)

    # Build lookup
    spec_by_id = {s.post_id: s for s in method_specs}

    results = []
    for group in grouping["groups"]:
        group_specs = [spec_by_id[pid] for pid in group["post_ids"] if pid in spec_by_id]
        if not group_specs:
            continue

        if len(group_specs) == 1:
            # Single source — no merge needed, just tag source_posts
            spec = group_specs[0]
            spec.source_posts = [spec.post_id]
            results.append(spec)
        else:
            # Multiple sources — merge via Grok
            specs_json = json.dumps(
                [s.model_dump(exclude={"post_id", "has_method", "skip_reason", "source_posts"}) for s in group_specs],
                indent=2,
            )
            merge_response = client.chat.completions.create(
                model="grok-4-1-fast-non-reasoning",
                max_tokens=8192,
                messages=[{"role": "user", "content": MERGE_PROMPT.format(specs_json=specs_json)}],
            )
            merge_text = merge_response.choices[0].message.content.strip()
            if merge_text.startswith("```"):
                merge_text = merge_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            merged_data = json.loads(merge_text)
            merged_data["post_id"] = group_specs[0].post_id
            merged_data["has_method"] = True
            merged_data["source_posts"] = [s.post_id for s in group_specs]
            results.append(MethodSpec(**merged_data))

    return results
