"""Deep per-video method analysis using Grok API."""

import json
import os
from openai import OpenAI
from stratalyzer.models import Extraction, MethodSpec

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("XAI_API_KEY", "")
        _client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    return _client


ANALYSIS_PROMPT = """You are analyzing a single short-form video from a content creator. Your job is to determine if this video teaches a specific METHOD, PROCESS, FRAMEWORK, or TECHNIQUE — and if so, produce a complete, detailed specification of that method.

This specification will be used to build software that EXECUTES the method. Precision matters. Do not summarize. Do not compress. Preserve every example, every number, every template, every visual reference.

Here is the video's data:

TRANSCRIPT:
{transcript}

ON-SCREEN TEXT:
{vision_text}

VISUAL DESCRIPTION:
{vision_description}

Return a JSON object. If the video teaches a method:

{{
  "has_method": true,
  "method_name": "Exact name the creator uses, or a descriptive name if unnamed",
  "method_type": "one of: writing_technique, production_technique, content_strategy, growth_tactic, monetization_system, editing_technique, analytics_diagnostic, ideation_system, branding_framework, other",
  "detailed_explanation": "Complete multi-paragraph explanation of what this method is and exactly how it works. Include every example, number, template, and visual reference from the video. Write as if explaining to a developer who will build software that does this. No compression.",
  "specific_examples": ["every concrete example the creator gives, quoted or paraphrased accurately"],
  "inputs": "what does someone need to START this method (a topic, a raw video, analytics data, etc.)",
  "outputs": "what does this method PRODUCE when completed (a script, an edited video, a content calendar, a hook, etc.)",
  "step_by_step": [
    {{
      "step": 1,
      "action": "what to do in this step",
      "detail": "exactly how to do it, with specifics from the video",
      "visual_reference": "what the creator showed on screen for this step, if anything"
    }}
  ],
  "rules": ["specific rules, constraints, or tips the creator mentions"],
  "creator_results": "any results or proof the creator mentions (view counts, revenue, etc.)",
  "related_topics": ["topic tags for grouping"]
}}

If the video does NOT teach a method (it's motivational, lifestyle, music-only, or just general advice without a specific process):

{{
  "has_method": false,
  "skip_reason": "brief reason why this isn't a method"
}}

Return ONLY the JSON object."""


def analyze_single_video(post_id: str, extraction: Extraction) -> MethodSpec:
    """Analyze a single video's full data and produce a MethodSpec."""
    transcript = extraction.transcript or "(no transcript)"
    vision_text = extraction.vision_text or "(no on-screen text captured)"
    vision_description = extraction.vision_description or "(no visual description)"

    prompt = ANALYSIS_PROMPT.format(
        transcript=transcript,
        vision_text=vision_text,
        vision_description=vision_description,
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="grok-4-1-fast-non-reasoning",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    data = json.loads(text)
    data["post_id"] = post_id
    return MethodSpec(**data)
