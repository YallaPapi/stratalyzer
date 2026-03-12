"""Deep per-video method analysis using Grok API."""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI
from stratalyzer.models import Extraction, MethodSpec, PostSummary

METHODS_CACHE_FILENAME = ".stratalyzer_methods_cache.json"
MAX_ANALYSIS_WORKERS = 10

_cache_lock = threading.Lock()

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


def analyze_all_videos(
    summaries: list[PostSummary],
    cache_dir: Path,
    progress=None,
    max_workers: int = MAX_ANALYSIS_WORKERS,
) -> list[MethodSpec]:
    """Analyze all videos in parallel, producing a MethodSpec per video."""
    cache_path = cache_dir / METHODS_CACHE_FILENAME
    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    results: list[MethodSpec] = []
    todo = []

    for summary in summaries:
        post_id = summary.post_id
        if post_id in cache:
            results.append(MethodSpec(**cache[post_id]))
        else:
            # Use the first extraction (each post is one video for junyuh-style creators)
            if summary.extractions:
                todo.append((post_id, summary.extractions[0]))

    if not todo:
        return results

    task_id = None
    if progress:
        task_id = progress.add_task("Analyzing methods (Grok)", total=len(todo))

    def _do_analysis(item):
        post_id, extraction = item
        return post_id, analyze_single_video(post_id, extraction)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_do_analysis, item): item for item in todo}
        for future in as_completed(futures):
            try:
                post_id, spec = future.result()
                results.append(spec)
                with _cache_lock:
                    cache[post_id] = spec.model_dump()
                    cache_path.write_text(
                        json.dumps(cache, indent=2, default=str),
                        encoding="utf-8",
                    )
            except Exception as e:
                post_id, _ = futures[future]
                import sys
                print(f"Method analysis error for {post_id}: {e}", file=sys.stderr)

            if progress and task_id is not None:
                progress.update(task_id, advance=1)

    return results
