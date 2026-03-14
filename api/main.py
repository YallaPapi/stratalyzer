"""FastAPI backend wrapping the Content Strategy Pipeline."""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import datetime
import json
import os
import re
import traceback
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

LOG_DIR = Path(__file__).parent / "logs"

TECHNICAL_PUBLIC_REPLACEMENTS = [
    (r"\bVast\.?ai\b", "cloud GPU"),
    (r"\bH100s?\b", "cloud GPU"),
    (r"\bCUDA\b", "render"),
    (r"\bSageAttention\b", "stability"),
    (r"\banti-detect(?: browser)?\b", "safe account"),
    (r"\bbrowser[- ]auth(?:enticated)?\b", "low-cost"),
    (r"\bLLM\b", "AI"),
    (r"\bRaspberry Pi\b", "cheap local device"),
    (r"\bSupergod\b", "AI system"),
    (r"\bOpenClaw\b", "automated outreach system"),
    (r"\bGeelark\b", "account setup tool"),
    (r"\bAdsPower\b", "account setup tool"),
    (r"\bIX Browser\b", "account setup tool"),
    (r"\bproxy(?: infra| stack| chaining| network| networks)?\b", "backend setup"),
    (r"\bComfyUI\b", "AI video workflow"),
    (r"\bSwarmUI\b", "AI video workflow"),
    (r"\bmulti-agent setup\b", "AI workflow"),
    (r"\bAI system multi-agent setup\b", "AI workflow"),
    (r"\bBrowser Agent Swarm\b", "AI work engine"),
    (r"\bbackend setup\b", "simple system"),
    (r"\bAPI-free\b", "without expensive software bills"),
]

MARKETING_SLOP_REPLACEMENTS = [
    (r"\bBrowser Agent Freedom System\b", "AI workflow that fits real work"),
    (r"\bZero Cost AI Multi-Agents\b", "lower-cost AI workflow"),
    (r"\bNomad Laptop Escape Blueprint\b", "run a one-man business with less grind"),
    (r"\bTrench Fail Proof Framework\b", "rebuild after getting burned"),
    (r"\b5K Hour Killer Pipeline\b", "way to buy back your time"),
    (r"\bVA Replacement Automation Kit\b", "automation for repetitive client work"),
    (r"\bContent Factory on Autopilot\b", "content system that actually ships"),
    (r"\bProxy Account Survival Hack\b", "safer account workflow"),
    (r"\bGPU Video Goldmine Workflow\b", "AI video workflow that actually ships"),
    (r"\bRebuild From Zero Roadmap\b", "plan to rebuild from zero"),
    (r"\bAI Automation Empire Builder\b", "AI automation advisory"),
    (r"\bAccelerator\b", "coaching"),
    (r"\bFreedom System\b", "practical system"),
    (r"\bFreedom Stack\b", "starter kit"),
    (r"\bBlueprint\b", "plan"),
    (r"\bGoldmine\b", "workflow"),
    (r"\bKiller Pipeline\b", "way to buy back time"),
    (r"\bSurvival Hack\b", "safer approach"),
    (r"\bon autopilot\b", "with less manual work"),
    (r"\bAutopilot\b", "less manual work"),
    (r"\bpassive\b", "more consistent"),
    (r"prints money on repeat", "can actually make money"),
    (r"scale accounts forever", "run accounts more safely"),
    (r"scales forever", "holds up better"),
    (r"fire your VAs and keep all the profits", "cut busywork and protect your margin"),
    (r"earn \$?20K passive from Thailand beaches", "make money without being glued to your laptop"),
    (r"work half the hours for double pay", "work fewer hours without capping your income"),
    (r"while you sleep", "without doing it all yourself"),
    (r"24/7 anywhere", "with less day-to-day work"),
    (r"platform apocalypse", "platform changes"),
    (r"\b6-figure systems\b", "durable systems"),
    (r"\bbulletproof\b", "more reliable"),
    (r"\bhands-free\b", "with less manual work"),
    (r"\bon repeat\b", "consistently"),
    (r"beach days back", "some free time back"),
]

MARKET_FACING_KEYS = {
    "core_message",
    "tagline",
    "who_uniqueness",
    "audience_connection",
    "message_breakdown",
    "niche_you_become",
    "description",
    "example_post",
    "positioned_version",
    "why_this_wins",
    "opening_script",
    "summary",
    "story_hook",
    "example_content_ideas",
    "content_ideas",
    "topics",
    "desires",
    "product_name",
    "product_idea",
    "freebie_idea",
    "free_resource",
    "freebie_concept",
    "resource_title",
    "next_cycle_product",
    "brand_identity",
    "results_promise",
}

QUALITY_ISSUE_PATTERNS = {
    "brand": [
        (r"\bbeaches?\b", "Beach lifestyle language is filler here."),
        (r"\bbattle-tested\b", "This sounds like generic marketing posture."),
        (r"\bfrom the trenches\b", "This phrase is overcooked creator branding."),
        (r"\bnomad life\b", "This phrase is generic lifestyle branding."),
        (r"\bpatong ai automator\b", "This identity label sounds made up."),
        (r"\bgrind\b", "This can slip into creator-marketing filler."),
        (r"\btravel freely\b", "This is vague aspirational fluff."),
        (r"\blaptop chain\b", "This phrasing sounds AI-written."),
        (r"\bno bs\b", "This is posture, not substance."),
        (r"\bbarefoot authentic\b", "This is cosplay detail, not value."),
    ],
    "title": [
        (r"\bfrom thailand\b", "Thailand/location is being used as filler instead of value."),
        (r"\bpatong\b", "Patong/location is being used as filler instead of value."),
        (r"\b40s nomad\b", "Identity label feels resume-like, not audience-facing."),
        (r"\bonlyfans agency\b", "This leans on backstory in a clunky way instead of leading with value."),
        (r"\bonlyfans management\b", "This leans on backstory in a clunky way instead of leading with value."),
        (r"\bapi costs?\b", "This is backend cost language, not front-door value."),
        (r"\bcheap local device\b", "This is technical implementation detail, not a hook."),
        (r"\bmulti-agents?\b", "This is technical stack language, not audience language."),
        (r"\bagents?\b", "This risks sounding like tool talk instead of a clear promise."),
        (r"\$\s?1\.5k\b", "Specific runway numbers are distracting here."),
        (r"\bovernight\b", "This sounds like hype, not believable creator language."),
        (r"\bhack\b", "Hack language reads cheap and generic."),
        (r"\bsdr\b", "This acronym is too insider-heavy for a front-door title."),
        (r"\bnomad\b", "Nomad identity is being used as filler instead of value."),
        (r"\bmuay thai\b", "Muay Thai should only stay when it sharpens the story."),
        (r"\bwithout vas?\b", "VAs language sounds operational, not scroll-stopping."),
        (r"\bprospect(?:ing)? clients?\b", "Prospecting language sounds like internal ops, not audience language."),
        (r"\bpublic[- ]data\b", "This sounds technical and backend-heavy."),
        (r"\bno team\b", "This is weak context unless paired with a sharper payoff."),
        (r"\bmuay thai.*beach\b", "This reads like manufactured lifestyle flavor."),
        (r"\bbulletproof\b", "This is marketing cliché."),
    ],
    "hook": [
        (r"\bwhile you sleep\b", "This is a cliché promise."),
        (r"\bon autopilot\b", "This is lazy marketing language."),
        (r"\bfrom thailand beach\b", "This is lifestyle cliché, not value."),
        (r"\bthailand beach\b", "This is lifestyle cliché, not value."),
        (r"\bAI handles the boring stuff\b", "This is vague filler instead of a concrete payoff."),
        (r"\bditch unreliable helpers\b", "This sounds salesy and weak."),
        (r"\bcut work hours in half\b", "This is a big promise that can sound fake."),
        (r"\bwork half the hours\b", "This is a big promise that can sound fake."),
        (r"\bclients come without chasing\b", "This promise is too slick and ad-like."),
        (r"\bAI that actually works\b", "This is generic filler, not a hook."),
        (r"\bovernight\b", "This sounds like hype, not believable creator language."),
        (r"\bwithout a team\b", "This is filler context, not a clear payoff."),
        (r"\breplace your vas? with code\b", "This sounds robotic and adversarial."),
        (r"\bclient hunting\b", "This sounds clunky and unnatural."),
        (r"\b20k\b", "Specific income brag language makes the hook feel fake."),
        (r"\btravel freedom\b", "This is generic lifestyle marketing language."),
        (r"\bcold calling\b", "This gets too tactical too fast for a hook."),
        (r"\bwithout lifting a finger\b", "This is a cliché promise."),
        (r"\bnomad freedom\b", "This is generic lifestyle marketing language."),
        (r"\bnomad dreams\b", "This is generic lifestyle marketing language."),
        (r"\bforever\b", "This usually reads as hype in hooks."),
        (r"\bbeach life\b", "This is lifestyle cliché, not value."),
        (r"\bwithout the grind\b", "This is generic creator-marketing filler."),
        (r"\bcut (?:my|your|our) (?:day|days|hours) in half\b", "This is a big promise that can sound fake."),
        (r"\bsolo freedom\b", "This is generic lifestyle marketing language."),
        (r"\bin thailand\b", "Location is filler here, not value."),
        (r"\bgave me the push\b", "This is empty testimonial-style filler."),
        (r"\bcontent pipelines\b", "This reads too technical for a hook."),
        (r"\blaptop-free\b", "This phrasing sounds unnatural."),
    ],
}

QUALITY_EDITOR_PROMPT = """You are a ruthless short-form copy editor. Your job is to rewrite weak creator-business copy so it sounds like a sharp human creator, not a LinkedIn marketer or AI ghostwriter.

Rules:
- Use plain spoken English.
- Keep the same number of lines.
- Preserve the core meaning, but rewrite any line that sounds vague, technical, cliché, inflated, or performative.
- Prefer pain, stakes, curiosity, and clear outcomes.
- Delete filler identity labels unless they genuinely sharpen the line.
- Never use phrases like "while you sleep", "on autopilot", "bulletproof", "empire builder", "from the trenches", "beach freedom", "public-data", "no team", "without VAs", or robotic creator-marketing language.
- If a line is already strong, keep it close.
- Prefer patterns like "how I get clients without hiring", "what rebuilding from zero taught me", "the first thing I'd automate if I were stuck again", "how I stopped doing everything myself".
- Avoid patterns like "run solo forever", "beach life", "Thailand freedom", "cut your hours in half", "without the grind", or "overnight".

Return ONLY a JSON array of rewritten strings, same length as input."""

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Content Strategy Pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _malformed_output_http_error(exc: InvalidAIResponseError, fallback_step: str) -> HTTPException:
    step_name = exc.step or fallback_step
    return HTTPException(
        status_code=502,
        detail=f"AI returned malformed structured output during {step_name}. The raw response was logged on the server.",
    )

# ---------------------------------------------------------------------------
# Model assignment per step
# ---------------------------------------------------------------------------

STEP_MODEL_MAP = {
    "step1": "Grok",
    "step2": "Grok",
    "step3": "Grok",
    "step4a": "Grok",
    "step4b": "Claude Sonnet",
    "step5": "GPT-5.3",
    "step6": "GPT-5.3",
}


def get_model(step_key: str, model_override: str = "auto") -> str:
    if model_override and model_override != "auto":
        return model_override
    return STEP_MODEL_MAP.get(step_key, "Grok")


# ---------------------------------------------------------------------------
# AI call helper (copied from pipeline, no Streamlit dependency)
# ---------------------------------------------------------------------------

class InvalidAIResponseError(Exception):
    """Raised when a model returns content we cannot parse into the required JSON."""

    def __init__(self, message: str, *, raw_response: str, step: str = "", detail: str = ""):
        super().__init__(message)
        self.raw_response = raw_response
        self.step = step
        self.detail = detail


def log_ai_call(app_name: str, step: str, system_prompt: str, user_message: str, raw_response: str, parsed_response):
    """Log AI call inputs and outputs to disk."""
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{app_name}_{timestamp}.json"

    log_entry = {
        "timestamp": timestamp,
        "app": app_name,
        "step": step,
        "input": {
            "system_prompt": system_prompt,
            "user_message": user_message,
        },
        "output": {
            "raw": raw_response,
            "parsed": parsed_response,
        }
    }

    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if isinstance(existing, list):
            existing.append(log_entry)
        else:
            existing = [existing, log_entry]
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    else:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)


def _extract_json_candidate(raw: str) -> str:
    """Extract the most likely JSON payload from a model response."""
    text = raw.strip()

    if "```" in text:
        fence_start = text.find("```")
        fence_end = text.rfind("```")
        if fence_end > fence_start:
            fenced = text[fence_start + 3:fence_end].strip()
            if "\n" in fenced:
                first_line, remainder = fenced.split("\n", 1)
                if first_line.strip().lower() in {"json", "javascript", "js"}:
                    text = remainder.strip()
                else:
                    text = fenced
            else:
                text = fenced

    decoder = json.JSONDecoder()
    for idx, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            _, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        candidate = text[idx:idx + end].strip()
        if candidate:
            return candidate

    return text


def normalize_public_facing_text(text: str) -> str:
    normalized = text
    for pattern, replacement in TECHNICAL_PUBLIC_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    for pattern, replacement in MARKETING_SLOP_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    normalized = re.sub(r"\bon [A-Za-z0-9._-]+ GPU\b", "on cloud GPU", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bhere's your\b", "here's how to", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfrom Thailand beaches\b", "while living abroad", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfrom a Thailand beach\b", "while living abroad", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bThailand beach\b", "living abroad", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bkeep all the profits\b", "improve your margin", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bquit time-trading and live free\b", "buy back your time", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"AI video workflow/AI video workflow workflows", "AI video workflow templates", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bwithout humans\b", "with less manual work", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\breplace VAs\b", "reduce repetitive work", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bwithout bans\b", "more safely", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bcut costs on AI tools\b", "use AI without wasting money", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bship systems that make money\b", "ship systems that support your income", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bhit higher months easier\b", "grow without adding more hours", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bGPU crash(?:es)?\b", "pipeline crash", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bjust? me grinding\b", "working through it solo", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s{2,}", " ", normalized).strip()
    return normalized


def normalize_public_facing_value(value, *, force: bool = False):
    if isinstance(value, str):
        return normalize_public_facing_text(value) if force else value
    if isinstance(value, list):
        return [normalize_public_facing_value(item, force=force) for item in value]
    if isinstance(value, dict):
        normalized = {}
        for key, nested in value.items():
            nested_force = force or key in MARKET_FACING_KEYS
            nested_value = normalize_public_facing_value(nested, force=nested_force)
            if key in {"product_name", "product_idea", "freebie_idea", "free_resource", "freebie_concept", "resource_title", "next_cycle_product"} and isinstance(nested_value, str):
                nested_value = cleanup_product_name(nested_value)
            normalized[key] = nested_value
        return normalized
    return value


def build_positioning_brief(step1_result: dict, step2_result: dict) -> str:
    avatar = step1_result.get("avatar", {}) if isinstance(step1_result, dict) else {}
    truth = step1_result.get("your_truth", {}) if isinstance(step1_result, dict) else {}
    branded = step2_result.get("branded_message", {}) if isinstance(step2_result, dict) else {}

    core_message = normalize_public_facing_text(step1_result.get("core_message", ""))
    audience = normalize_public_facing_text(avatar.get("demographics", "solo operators who want more leverage"))
    struggles = normalize_public_facing_text(avatar.get("currently_struggling_with", "doing everything themselves and capped by time"))
    credibility = normalize_public_facing_text(truth.get("summary", "Built real systems after real business mistakes."))
    tagline = normalize_public_facing_text(branded.get("tagline", ""))

    return (
        "FRONT-DOOR POSITIONING:\n"
        f"- Audience: {audience}\n"
        f"- Core promise: {core_message}\n"
        f"- Real pain to lead with: {struggles}\n"
        "- Outcomes to emphasize: get clients without hiring, buy back time, make AI useful in real work, run a one-person business more smoothly, rebuild after getting burned.\n"
        f"- Creator credibility: {credibility}\n"
        f"- Tagline flavor only: {tagline}\n"
        "- Use technical details as proof only after the hook lands.\n"
        "- Do NOT center titles, hooks, or offer names on rendering tools, account-protection tactics, proxies, bans, APIs, or tool names unless the buyer explicitly wants that.\n"
    )


def find_quality_issues(text: str, *, kind: str) -> list[str]:
    lowered = text.strip()
    issues = []
    for pattern, description in QUALITY_ISSUE_PATTERNS.get(kind, []):
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            issues.append(description)
    return issues


def translate_content_idea_to_market_language(text: str) -> str:
    lowered = text.lower()

    if any(word in lowered for word in ["prospect", "lead", "sdr", "outreach"]):
        return "how I get clients without hiring a sales team"
    if any(word in lowered for word in ["video", "reels", "shorts", "lipsync", "content"]):
        return "how I make content without editing all day"
    if any(word in lowered for word in ["partner", "partnership", "rebuild", "onlyfans"]):
        return "what rebuilding after business fallout taught me"
    if any(word in lowered for word in ["agency", "zero", "start over", "blow up", "wiped out"]):
        return "what rebuilding after business fallout taught me"
    if any(word in lowered for word in ["patong", "thailand", "muay thai", "nomad"]):
        return "how I stay sane while rebuilding solo"
    if any(word in lowered for word in ["automation", "workflow", "agent", "ai"]):
        return "how I use AI to buy back my time"
    return normalize_public_facing_text(text)


def cleanup_product_name(text: str) -> str:
    lowered = text.lower()
    if ("autonomous agency" in lowered and "course" in lowered) or ("solo agency automation" in lowered and "course" in lowered):
        return "Solo Operator Automation Course"
    if "solo agency automation plan" in lowered:
        return "Solo Operator Automation Course"
    if "video content system course" in lowered:
        return "Solo Operator Automation Course"
    if "pipeline builder" in lowered or ("content pipeline" in lowered and "kit" in lowered):
        return "AI Content Automation Plan"
    if "solo operator automation plan" in lowered:
        return "AI Business Rebuild Coaching"
    if "business automation coaching" in lowered:
        return "AI Business Rebuild Coaching"
    if "prospect" in lowered or "lead" in lowered:
        return "AI Prospecting Workflow Kit"
    if "content automation" in lowered or ("content" in lowered and "automation" in lowered):
        return "AI Content Automation Plan"
    if "audit" in lowered and "checklist" in lowered:
        return "AI Automation Quick Audit Checklist"
    if "checklist" in lowered and "quickstart" in lowered:
        return "AI Automation Starter Checklist"
    if "coaching" in lowered and ("automation" in lowered or "business automation" in lowered):
        return "AI Business Automation Coaching"

    if ":" in text:
        text = text.split(":", 1)[0].strip()

    words = []
    for word in text.split():
        if word.isupper() or any(char.isdigit() for char in word):
            words.append(word)
        elif word.lower() in {"ai", "va", "sdr"}:
            words.append(word.upper())
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def extract_from_brief(positioning_brief: str, label: str) -> str:
    match = re.search(rf"- {re.escape(label)}: (.+)", positioning_brief)
    return match.group(1).strip() if match else ""


def derive_tagline_from_promise(core_promise: str) -> str:
    lowered = core_promise.lower()
    if "work less" in lowered and "live more" in lowered:
        return "Work Less. Live More."
    if "get clients" in lowered and "hiring" in lowered:
        return "Get Clients Without Hiring."
    if "buy back" in lowered and "time" in lowered:
        return "Buy Back Your Time."
    return "Automate the work. Keep your life."


def simplify_core_message(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["live anywhere", "work less", "automation", "ai", "business"]):
        return "I show solo entrepreneurs how to automate the work that keeps the business stuck on their time."
    return normalize_public_facing_text(text)


def simplify_real_pain(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["time", "$5k", "bandwidth", "doing everything", "bandwidth caps"]):
        return "doing everything yourself and watching the business cap out"
    if "client" in lowered:
        return "being buried in client work with no room to grow"
    return "doing everything yourself and feeling stuck"


def dedupe_preserve_order(items: list[str]) -> list[str]:
    unique = []
    for item in items:
        if item not in unique:
            unique.append(item)
    return unique


def classify_market_topic(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["client", "lead", "sales", "prospect", "outreach"]):
        return "clients"
    if any(word in lowered for word in ["content", "edit", "video", "post", "reels", "shorts", "hook"]):
        return "content"
    if any(word in lowered for word in ["rebuild", "partner", "fallout", "blowup", "onlyfans"]):
        return "rebuild"
    if any(word in lowered for word in ["abroad", "thailand", "nomad", "travel", "muay thai"]):
        return "abroad"
    if any(word in lowered for word in ["time", "everything", "automation", "ai"]):
        return "time"
    return "systems"


def step1_pillar_description(pillar_name: str) -> str:
    lowered = pillar_name.lower()
    if "truth" in lowered or "rebuild" in lowered or "lesson" in lowered or "trench" in lowered or "scar" in lowered:
        return "Share what went wrong, what changed, and what other solo operators should avoid."
    if "build" in lowered or "automate" in lowered or "ai" in lowered:
        return "Show the systems that save time, bring in clients, or remove repetitive work."
    if "nomad" in lowered or "life" in lowered:
        return "Show how you keep work under control while living abroad."
    if "content" in lowered or "release" in lowered:
        return "Show how you turn one idea into useful content without doing it all by hand."
    return "Show the practical lessons, systems, and stories people can actually use."


def simplify_truth_angle(angle: str, story_hook: str) -> tuple[str, str]:
    lowered = f"{angle} {story_hook}".lower()
    if any(token in lowered for token in ["2am", "debug", "sageattention", "h100", "cuda", "gpu", "pipeline"]):
        return (
            "Late-Night Fixes",
            "What fixing broken systems late at night taught me about keeping things simple.",
        )
    if any(token in lowered for token in ["partner", "wipeout", "betrayal", "blow", "zero"]):
        return (
            "Rebuilding From Zero",
            "How losing the business changed the way I build now.",
        )
    if any(token in lowered for token in ["onlyfans", "exit", "agency"]):
        return (
            "Leaving The Old Model",
            "Why I walked away from a business that made money but had no future.",
        )
    if any(token in lowered for token in ["account", "anonymous", "shadow", "public"]):
        return (
            "Leaving The Back Room",
            "What changed when I stopped hiding behind the work and started showing it.",
        )
    if any(token in lowered for token in ["perfection", "planning", "shipping", "over-engineer"]):
        return (
            "Overthinking The Work",
            "How overplanning kept me stuck and what finally got me to ship.",
        )
    if any(token in lowered for token in ["nomad", "thailand", "muay thai", "sane"]):
        return (
            "Keeping My Head Straight",
            "How training and a simpler routine stopped work from taking over my life.",
        )
    return (
        normalize_public_facing_text(angle).title(),
        normalize_public_facing_text(story_hook),
    )


def simplify_truth_summary(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["partner", "rebuild", "thailand", "onlyfans", "automation", "agent", "gpu", "browser", "proxy"]):
        return "I spent years building messy online businesses, got burned hard, rebuilt solo, and now show what to automate first because I learned the hard way what breaks."
    return normalize_public_facing_text(text)


def build_step3_title(base: str, source_text: str, category: str, index: int) -> str:
    lowered = source_text.lower()
    if category == "clients":
        titles = [
            "how I get clients without adding more hours",
            "what I would automate first if I had to find clients again",
            "the client workflow I'd fix before hiring anyone",
            "how I stopped letting lead gen eat the whole week",
        ]
        return titles[index % len(titles)]
    if category == "content":
        if any(token in lowered for token in ["burn", "overwork", "hate"]):
            titles = [
                "the content setup I use when I do not want to burn out",
                "the part of content I stopped doing by hand",
            ]
            return titles[min(index, len(titles) - 1)]
        titles = [
            "how I post without editing all day",
            "how I keep posting without living in the editor",
            "the part of content I stopped doing by hand",
        ]
        return titles[index % len(titles)]
    if category == "time":
        titles = [
            "the first thing I automated to stop doing everything myself",
            "how I bought back time without slowing the business down",
            "the workflow I fixed when I was doing too much myself",
            "what I automated first when the business started eating my week",
        ]
        return titles[index % len(titles)]
    if category == "rebuild":
        titles = [
            "what rebuilding from zero taught me about simple systems",
            "what I stopped doing after my business blew up",
            "the one rule I kept after rebuilding from zero",
            "what I learned when the old business stopped working",
        ]
        return titles[index % len(titles)]
    if category == "abroad":
        titles = [
            "how I keep the business moving while living abroad",
            "what living abroad taught me about simplifying work",
            "the routine that keeps work under control while I travel",
            "how I stopped work from taking over life abroad",
        ]
        return titles[index % len(titles)]
    return "what I stripped out when the business stopped working" if index == 0 else "the one system I kept when I had to start over"


def build_step3_opening_script(title: str, category: str) -> str:
    if title == "how I get clients without adding more hours":
        return "If I had to find clients again without working more hours, this is the first system I'd build. It takes a job I used to do by hand and turns it into something repeatable."
    if title == "what I would automate first if I had to find clients again":
        return "If I had to start over and find clients again, I would not begin with more outreach. I'd start with the part of the workflow that keeps eating time every single week."
    if title == "the content setup I use when I do not want to burn out":
        return "I got tired of spending half the day editing instead of publishing. This is the setup I use to keep posting without letting content take over the whole week."
    if title == "how I post without editing all day":
        return "I wanted content to stop eating half my week. This is the setup I use to keep publishing without living in the editor."
    if title == "the first thing I automated to stop doing everything myself":
        return "The fastest way to stay stuck is to keep every task on your own plate. This is the first piece I automated when I needed the business to move without me touching every step."
    if title == "how I bought back time without slowing the business down":
        return "I did not need more apps or more hustle. I needed one system that took a recurring task off my plate without slowing everything else down."
    if title == "what rebuilding from zero taught me about simple systems":
        return "Starting over made the bloated stuff obvious fast. This is what I kept, what I dropped, and what I would build first now."
    if title == "what I stopped doing after my business blew up":
        return "When the old business fell apart, I had to get honest about what was wasting time. These are the habits and systems I stopped carrying into the rebuild."
    if title == "the one rule I kept after rebuilding from zero":
        return "Starting over stripped the business down fast. This is the one rule I kept because it made everything easier to run."
    if title == "what I learned when the old business stopped working":
        return "When the old setup stopped working, it forced me to see what was actually useful. This is what I would carry into a rebuild now."
    if title == "how I keep the business moving while living abroad":
        return "Living abroad forced me to stop relying on constant manual work. This is the simple setup I use to keep the business moving without being glued to the laptop."
    if title == "what living abroad taught me about simplifying work":
        return "You find out fast which parts of the business are real and which ones are noise when you live abroad. This is what I simplified first."
    if title == "how I keep posting without living in the editor":
        return "I wanted content to stop taking over the whole week. This is the workflow I use when I need to post consistently without getting stuck editing."
    if title == "the part of content I stopped doing by hand":
        return "The biggest shift in my content process came from removing one repetitive step. This is the part I stopped doing by hand first."
    if title == "the client workflow I'd fix before hiring anyone":
        return "Before adding people, I would fix the part of client work that keeps stealing hours. This is the workflow I'd clean up first."
    if title == "how I stopped letting lead gen eat the whole week":
        return "Lead generation used to sprawl across the whole week. This is the change that made it feel manageable again."
    if title == "the workflow I fixed when I was doing too much myself":
        return "The business got lighter once I stopped carrying this task myself. This is the workflow I'd fix first if I were overloaded again."
    if title == "what I automated first when the business started eating my week":
        return "Once the business started swallowing the whole week, this was the first task I automated. It made the rest of the work easier to handle."
    if title == "the routine that keeps work under control while I travel":
        return "Travel makes weak systems obvious fast. This is the routine that keeps work under control without turning every day into cleanup."
    if title == "how I stopped work from taking over life abroad":
        return "Living abroad did not matter if work still owned the day. This is the change that made the business easier to live with."
    if category == "clients":
        return "This is the first workflow I'd fix if getting clients was still taking too much of my week. It is simple, repeatable, and does not need a bigger team."
    if category == "content":
        return "This is the content workflow I keep coming back to when I want to stay consistent without creating more busywork."
    if category == "rebuild":
        return "This is one of the biggest lessons I carried into the rebuild. It made the business simpler and easier to keep moving."
    return "This is the setup I use when I want the business to run with less manual work."


def build_step3_why_this_wins(category: str) -> str:
    if category == "clients":
        return "It leads with an outcome people already want instead of the backend mechanics behind it."
    if category == "content":
        return "It turns a messy creator workflow into a pain people already recognize."
    if category == "rebuild":
        return "It uses real scars as proof without making the backstory the whole point."
    if category == "abroad":
        return "It keeps the lifestyle context as proof while still leading with a useful takeaway."
    return "It translates backend know-how into a clear front-door idea people can understand fast."


STEP4_HOOK_FALLBACKS = [
    "If you're doing everything yourself, this is the first thing I'd automate.",
    "If your income only moves when you work more, this is the workflow I'd fix first.",
    "If client work eats your whole week, this is how I'd buy back time first.",
    "If AI still feels confusing in your business, this is where I'd start using it.",
    "If you keep drowning in repetitive work, this is the first system I'd build.",
    "If content takes too long to make, this is the part I'd stop doing by hand.",
    "If you're stuck at the same revenue because you're the bottleneck, start here.",
    "If your business only moves when you push every task forward, fix this first.",
    "If hiring still feels too early, this is how I'd lighten the workload first.",
    "If you're burned out and still behind, this is the first thing I'd simplify.",
    "If you want more clients without adding more hours, this is where I'd begin.",
    "If every task still needs you, this is the first handoff I'd build.",
    "If your systems look smart but never ship, simplify this part first.",
    "If you're testing AI tools but nothing changes, use them here first.",
    "If your income feels shaky because everything depends on you, start here.",
    "If you're tired of rebuilding the same week over and over, automate this part.",
    "If you have no extra hours left, this is where I'd buy them back.",
    "If manual follow-up keeps slowing the business down, this is the first fix I'd make.",
    "If you want the business to run smoother without more people, start here.",
    "If the day disappears into small tasks, this is the first one I'd take off your plate.",
]

STEP4_HOOK_LIBRARY = [
    "If you're still doing lead gen by hand, this is the first workflow I'd automate.",
    "If you want more clients without adding more hours, start here.",
    "If your week disappears into client work, this is the first task I'd stop doing myself.",
    "If your business only grows when you grind harder, this is the system I'd fix first.",
    "If you keep testing AI tools but nothing changes, use them for this job first.",
    "If content always gets pushed to later, this is the part I'd stop doing by hand.",
    "If posting feels harder than it should, this is the content workflow I'd build first.",
    "If you never have time to make content, this is how I'd lighten that part of the week.",
    "If you're burned out from doing everything yourself, automate this before anything else.",
    "If your income feels fragile because everything depends on you, start here.",
    "If one bad week wrecks the whole business, this is the system I'd tighten first.",
    "If you keep rebuilding the same messy week over and over, automate this part.",
    "If hiring still feels too early, this is how I'd take work off your plate first.",
    "If every task still needs you, this is the first handoff I'd build.",
    "If your business looks busy but not simple, fix this workflow first.",
    "If you want more room to think, stop doing this task by hand.",
    "If you're stuck at the same revenue because you're the bottleneck, start here.",
    "If your tools look smart but your days still feel chaotic, automate this part first.",
    "If you want a one-person business that runs smoother, this is where I'd begin.",
    "If you're tired of work spilling into everything, this is the first system I'd build.",
]


def refine_hook_lines(lines: list[str], *, kind: str, positioning_brief: str, model_choice: str) -> list[str]:
    if not lines:
        return []

    if kind != "hook":
        return rewrite_lines_with_quality_gate(
            lines,
            kind=kind,
            positioning_brief=positioning_brief,
            model_choice=model_choice,
        )

    cleaned = [normalize_public_facing_text(str(line)).strip() for line in lines]
    refined = []
    used = set()
    fallback_index = 0

    for line in cleaned:
        issues = find_quality_issues(line, kind="hook")
        candidate = line
        if candidate in used or issues:
            while fallback_index < len(STEP4_HOOK_FALLBACKS) and STEP4_HOOK_FALLBACKS[fallback_index] in used:
                fallback_index += 1
            if fallback_index < len(STEP4_HOOK_FALLBACKS):
                candidate = STEP4_HOOK_FALLBACKS[fallback_index]
                fallback_index += 1
        refined.append(candidate)
        used.add(candidate)

    while len(refined) < len(lines):
        while fallback_index < len(STEP4_HOOK_FALLBACKS) and STEP4_HOOK_FALLBACKS[fallback_index] in used:
            fallback_index += 1
        if fallback_index >= len(STEP4_HOOK_FALLBACKS):
            break
        refined.append(STEP4_HOOK_FALLBACKS[fallback_index])
        used.add(STEP4_HOOK_FALLBACKS[fallback_index])
        fallback_index += 1

    return refined[: len(lines)]


def simplify_offer_content_idea(text: str) -> str:
    category = classify_market_topic(text)
    if category == "clients":
        return "Doing everything yourself? This is the first part of the work I'd automate."
    if category == "content":
        return "Content taking too long? This is the part I'd stop doing by hand first."
    if category == "rebuild":
        return "What a bad business chapter taught me about building something simpler."
    if category == "abroad":
        return "Living abroad? Here's how I'd keep the business moving without more chaos."
    return "If your business still depends on you for every little task, this is where I'd start simplifying."


def build_step4_hooks(step1_result: dict, step2_result: dict, distill_result: dict) -> list[str]:
    return STEP4_HOOK_LIBRARY[:20]


def build_step6_hooks(step5_results: dict) -> list[str]:
    available_names = []
    for fw_name, fw_data in step5_results.items():
        if fw_name == "DOSER":
            own = fw_data.get("own", {})
            sell = fw_data.get("sell", {})
            for key in ("freebie_idea",):
                if own.get(key):
                    available_names.append(str(own[key]))
            for key in ("product_idea",):
                if sell.get(key):
                    available_names.append(str(sell[key]))
        if fw_name == "Layered Offers":
            free = fw_data.get("free_value_layer", {})
            if free.get("free_resource"):
                available_names.append(str(free["free_resource"]))
            for tier_key in ("tier_1_low_ticket", "tier_2_mid_ticket", "tier_3_high_ticket"):
                tier = fw_data.get(tier_key, {})
                if tier.get("product_name"):
                    available_names.append(str(tier["product_name"]))

    names = dedupe_preserve_order([cleanup_product_name(name) for name in available_names if name])
    templates = {
        "AI Prospecting Workflow Kit": [
            "If you're still doing lead gen by hand, start with the AI Prospecting Workflow Kit.",
            "If finding clients still eats too much of your week, start with the AI Prospecting Workflow Kit.",
        ],
        "AI Automation Quick Audit Checklist": [
            "If you don't know what to automate first, grab the AI Automation Quick Audit Checklist.",
            "If the business feels messy and manual, start with the AI Automation Quick Audit Checklist.",
        ],
        "AI Automation Starter Checklist": [
            "If you want the simplest place to begin, grab the AI Automation Starter Checklist.",
            "If you need a quick reset before building anything bigger, start with the AI Automation Starter Checklist.",
        ],
        "AI Automation Niche Finder Worksheet": [
            "If you keep second-guessing what offer to build, start with the AI Automation Niche Finder Worksheet.",
        ],
        "Solo Operator Automation Course": [
            "If everything in the business still runs through you, start with the Solo Operator Automation Course.",
            "If you want the whole workflow mapped out, start with the Solo Operator Automation Course.",
        ],
        "AI Business Rebuild Coaching": [
            "If you want help simplifying the whole business, start with AI Business Rebuild Coaching.",
        ],
        "AI Content Automation Plan": [
            "If content keeps falling behind, start with the AI Content Automation Plan.",
        ],
    }

    hooks = []
    for name in names:
        hooks.extend(templates.get(name, [f"If you need a simpler starting point, begin with the {name}."]))
    fallback = [
        "If your week disappears into repetitive work, start with the AI Prospecting Workflow Kit.",
        "If you want a clearer first step before buying bigger help, grab the AI Automation Quick Audit Checklist.",
        "If your systems still feel messy, start with the Solo Operator Automation Course.",
        "If you need to simplify the business before you scale it, AI Business Rebuild Coaching is built for that.",
    ]
    hooks.extend(fallback)
    return dedupe_preserve_order(hooks)[:10]


def refine_step3_output(result: list[dict], positioning_brief: str, *, model_choice: str) -> list[dict]:
    if not isinstance(result, list):
        return result

    category_counts = {}
    for item in result:
        if not isinstance(item, dict):
            continue
        generic = translate_content_idea_to_market_language(str(item.get("generic_version", "") or item.get("positioned_version", "")))
        source_text = " ".join(
            str(item.get(key, ""))
            for key in ("positioned_version", "why_this_wins", "opening_script")
        )
        category = classify_market_topic(generic)
        index = category_counts.get(category, 0)
        category_counts[category] = index + 1

        title = build_step3_title(generic, source_text, category, index)
        item["generic_version"] = generic
        item["positioned_version"] = title
        item["why_this_wins"] = build_step3_why_this_wins(category)
        item["opening_script"] = build_step3_opening_script(title, category)

    return result


def refine_step6_output(hooks: list[str], positioning_brief: str, *, model_choice: str) -> list[str]:
    product_patterns = [
        "AI Prospecting Workflow Kit",
        "AI Automation Quick Audit Checklist",
        "AI Automation Starter Checklist",
        "AI Automation Niche Finder Worksheet",
        "Solo Operator Automation Course",
        "AI Business Rebuild Coaching",
        "AI Content Automation Plan",
    ]
    fallbacks = {
        "AI Prospecting Workflow Kit": [
            "If finding clients still eats too much of your week, start with the AI Prospecting Workflow Kit.",
            "If everything in your business still needs you, the AI Prospecting Workflow Kit is the first place I would start.",
            "If you know you need a better client workflow, start with the AI Prospecting Workflow Kit.",
        ],
        "AI Automation Quick Audit Checklist": [
            "If your business feels messy and manual, start with the AI Automation Quick Audit Checklist.",
            "If you are not sure what to automate first, grab the AI Automation Quick Audit Checklist.",
        ],
        "AI Automation Starter Checklist": [
            "If you want a simple place to start, grab the AI Automation Starter Checklist.",
        ],
        "AI Automation Niche Finder Worksheet": [
            "If you keep second-guessing what offer to build, start with the AI Automation Niche Finder Worksheet.",
        ],
        "Solo Operator Automation Course": [
            "If your business keeps stalling because everything runs through you, start with the Solo Operator Automation Course.",
        ],
        "AI Business Rebuild Coaching": [
            "If you want help simplifying the whole business, the AI Business Rebuild Coaching is where I'd start.",
        ],
        "AI Content Automation Plan": [
            "If content keeps falling behind, start with the AI Content Automation Plan.",
        ],
    }

    refined = []
    product_indices = {}
    used = set()
    for hook in hooks:
        cleaned = normalize_public_facing_text(str(hook))
        matched_product = next((name for name in product_patterns if name in cleaned), None)
        candidate = cleaned

        issues = find_quality_issues(cleaned, kind="hook")
        if matched_product and issues:
            variants = fallbacks.get(matched_product, [f"If you need a simpler place to start, begin with the {matched_product}."])
            variant_index = product_indices.get(matched_product, 0)
            candidate = variants[min(variant_index, len(variants) - 1)]
            product_indices[matched_product] = variant_index + 1
        elif matched_product and "client" in cleaned.lower():
            variants = fallbacks.get(matched_product, [candidate])
            variant_index = product_indices.get(matched_product, 0)
            candidate = variants[min(variant_index, len(variants) - 1)]
            product_indices[matched_product] = variant_index + 1

        if candidate in used and matched_product:
            variants = fallbacks.get(matched_product, [candidate])
            variant_index = product_indices.get(matched_product, 0)
            candidate = variants[min(variant_index, len(variants) - 1)]
            product_indices[matched_product] = variant_index + 1

        refined.append(candidate)
        used.add(candidate)

    return refined


def rewrite_lines_with_quality_gate(lines: list[str], *, kind: str, positioning_brief: str, model_choice: str, force: bool = False) -> list[str]:
    if not lines:
        return lines

    current = lines[:]
    for _ in range(3):
        issue_map = {
            idx: find_quality_issues(line, kind=kind)
            for idx, line in enumerate(current)
        }
        flagged = {idx: issues for idx, issues in issue_map.items() if issues}
        if not flagged and not force:
            return current
        if force and not flagged:
            flagged = {idx: ["This line still needs rewriting into sharper public-facing language."] for idx in range(len(current))}

        issue_notes = "\n".join(
            f"- Line {idx + 1}: {current[idx]} :: {'; '.join(issues)}"
            for idx, issues in flagged.items()
        )
        user_message = (
            f"POSITIONING BRIEF:\n{positioning_brief}\n\n"
            f"KIND: {kind}\n"
            "Rewrite only the weak lines below so they sound natural, sharp, and audience-facing.\n"
            "Keep the same number of lines and preserve the overall meaning.\n\n"
            f"QUALITY ISSUES:\n{issue_notes}\n\n"
            "LINES:\n"
            + json.dumps(current, ensure_ascii=False)
        )
        rewritten = call_ai(
            QUALITY_EDITOR_PROMPT,
            user_message,
            max_tokens=4096,
            step=f"quality_edit_{kind}",
            model_choice=model_choice,
        )
        if isinstance(rewritten, list) and len(rewritten) == len(current):
            current = [normalize_public_facing_text(str(line)) for line in rewritten]

    return current


def refine_step2_output(result: dict, positioning_brief: str, *, model_choice: str) -> dict:
    core_promise = extract_from_brief(positioning_brief, "Core promise")
    real_pain = extract_from_brief(positioning_brief, "Real pain to lead with")
    credibility = extract_from_brief(positioning_brief, "Creator credibility")

    branded = result.get("branded_message", {})
    if core_promise:
        branded["core_message"] = simplify_core_message(core_promise)
        branded["tagline"] = derive_tagline_from_promise(core_promise)
    else:
        lines = []
        keys = []
        for key in ("core_message", "tagline"):
            value = branded.get(key)
            if isinstance(value, str):
                lines.append(value)
                keys.append(key)
        if lines:
            rewritten = rewrite_lines_with_quality_gate(
                lines,
                kind="brand",
                positioning_brief=positioning_brief,
                model_choice=model_choice,
                force=True,
            )
            for key, new_value in zip(keys, rewritten):
                branded[key] = new_value

    if credibility:
        branded["who_uniqueness"] = credibility
    if real_pain:
        pain_clause = simplify_real_pain(real_pain)
        branded["audience_connection"] = f"If you're stuck {pain_clause}, this will feel familiar fast."
        branded["message_breakdown"] = (
            "The message is simple: automate the work that traps you, keep control, and build something that doesn't depend on constant grind."
        )
    result["branded_message"] = branded

    if "blueprint" in result and isinstance(result["blueprint"], dict):
        if core_promise:
            result["blueprint"]["niche_you_become"] = "The solo operator who rebuilt with automation."
        else:
            niche = result["blueprint"].get("niche_you_become", "")
            rewritten = rewrite_lines_with_quality_gate(
                [str(niche)],
                kind="brand",
                positioning_brief=positioning_brief,
                model_choice=model_choice,
                force=True,
            )
            if rewritten:
                result["blueprint"]["niche_you_become"] = rewritten[0]

        for pillar in result["blueprint"].get("content_pillars", []):
            pillar_name = str(pillar.get("pillar", "")).lower()
            if "rebuild" in pillar_name or "lesson" in pillar_name or "trench" in pillar_name or "truth" in pillar_name or "scar" in pillar_name:
                pillar["description"] = "Share what went wrong, what changed, and what other solo operators should avoid."
                pillar["example_post"] = "what rebuilding from zero taught me about simple systems"
            elif "build" in pillar_name or "automate" in pillar_name:
                pillar["description"] = "Show the systems that save time, win clients, or remove repetitive work."
                pillar["example_post"] = "how I get clients without adding more hours"
            elif "nomad" in pillar_name or "life" in pillar_name:
                pillar["description"] = "Show how you keep work under control while living abroad."
                pillar["example_post"] = "how I keep work under control while living abroad"
            elif "content" in pillar_name or "release" in pillar_name:
                pillar["description"] = "Show how you create and publish content without doing it all by hand."
                pillar["example_post"] = "how I make content without editing all day"
            else:
                example_post = pillar.get("example_post")
                if isinstance(example_post, str):
                    pillar["example_post"] = translate_content_idea_to_market_language(example_post)

        visual_identity = result["blueprint"].get("visual_identity")
        if isinstance(visual_identity, dict):
            visual_identity["style_direction"] = "Screen shares, desk shots, voiceover, and a few training clips. Keep it clean, direct, and unpolished."
            result["blueprint"]["visual_identity"] = visual_identity

        operational_template = result["blueprint"].get("operational_template")
        if isinstance(operational_template, dict):
            operational_template["posting_rhythm"] = "4-5 short videos a week, with most posts focused on practical systems and a smaller number on personal lessons."
            operational_template["content_creation_workflow"] = "Pick one useful idea, record it simply, edit fast, and publish before you overthink it."
            operational_template["authenticity_anchors"] = "Use screen recordings, clear explanations, and honest recaps of what worked and what did not."
            result["blueprint"]["operational_template"] = operational_template

    return result


def refine_step1_output(result: dict, positioning_brief: str, *, model_choice: str) -> dict:
    if isinstance(result.get("core_message"), str):
        result["core_message"] = simplify_core_message(result["core_message"])

    for pillar in result.get("content_pillars", []):
        pillar["description"] = step1_pillar_description(str(pillar.get("name", "")))
        if pillar.get("is_anchor"):
            pillar["anchor_rationale"] = "Make this the main pillar because useful system breakdowns give the clearest proof of what you do and the easiest reason to follow."
        ideas = pillar.get("example_content_ideas", [])
        if isinstance(ideas, list):
            translated = [
                translate_content_idea_to_market_language(str(idea))
                for idea in ideas
            ]
            unique = []
            for idea in translated:
                if idea not in unique:
                    unique.append(idea)
            pillar_name = str(pillar.get("name", "")).upper()
            if "BUILD" in pillar_name or "AI" in pillar_name or "AUTOMATE" in pillar_name:
                fallbacks = [
                    "how I get clients without hiring a sales team",
                    "how I use AI to buy back my time",
                    "how I make content without editing all day",
                ]
            elif "REBUILD" in pillar_name or "TRUTH" in pillar_name or "LESSON" in pillar_name:
                fallbacks = [
                    "what rebuilding after business fallout taught me",
                    "how I rebuilt after trusting the wrong partner",
                    "signs your business model is capping out",
                ]
            elif "NOMAD" in pillar_name or "LIFE" in pillar_name:
                fallbacks = [
                    "how I stay sane while rebuilding solo",
                    "how I work less without giving up travel",
                    "how I keep a business moving from Thailand",
                ]
            elif "CONTENT" in pillar_name or "RELEASE" in pillar_name:
                fallbacks = [
                    "how I make content without editing all day",
                    "how I turn one script into a week of content",
                    "how I ship content without a team",
                ]
            else:
                fallbacks = []
            for fallback in fallbacks:
                if fallback not in unique:
                    unique.append(fallback)
                if len(unique) >= 3:
                    break
            pillar["example_content_ideas"] = unique[: max(3, len(unique))]

    truth = result.get("your_truth", {})
    summary = truth.get("summary")
    needs_summary_rewrite = (
        isinstance(summary, str)
        and (
            bool(find_quality_issues(summary, kind="brand"))
            or any(
                phrase in summary.lower()
                for phrase in ["cheap local device", "api costs", "cloud gpu", "ai system", "multi-agent"]
            )
        )
    )
    if needs_summary_rewrite:
        rewritten = rewrite_lines_with_quality_gate(
            [summary],
            kind="brand",
            positioning_brief=positioning_brief,
            model_choice=model_choice,
            force=True,
        )
        if rewritten:
            truth["summary"] = simplify_truth_summary(rewritten[0])
            result["your_truth"] = truth
    elif isinstance(summary, str):
        truth["summary"] = simplify_truth_summary(summary)
        result["your_truth"] = truth

    angles = truth.get("most_powerful_content_angles", [])
    if isinstance(angles, list):
        for angle_data in angles:
            if not isinstance(angle_data, dict):
                continue
            angle, hook = simplify_truth_angle(
                str(angle_data.get("angle", "")),
                str(angle_data.get("story_hook", "")),
            )
            angle_data["angle"] = angle
            angle_data["story_hook"] = hook

    weekly = result.get("weekly_balance", {})
    if isinstance(weekly, dict) and weekly.get("rationale"):
        weekly["rationale"] = "Let the practical build content carry the schedule, then use the personal stories to make people care."
        result["weekly_balance"] = weekly

    return result


def refine_step5_output(result: dict) -> dict:
    normalized = normalize_public_facing_value(result)

    doser = normalized.get("DOSER", {}) if isinstance(normalized, dict) else {}
    layered = normalized.get("Layered Offers", {}) if isinstance(normalized, dict) else {}

    freebie = doser.get("own", {}).get("freebie_idea")
    product = doser.get("sell", {}).get("product_idea")
    if isinstance(freebie, str) and isinstance(product, str) and freebie == product:
        doser.setdefault("own", {})["freebie_idea"] = "AI Automation Starter Checklist"

    document = doser.get("document", {})
    if isinstance(document, dict):
        document["what_to_document"] = "Document the systems you're building, the mistakes you made, and the simple fixes that saved you time."
        if isinstance(document.get("content_ideas"), list):
            document["content_ideas"] = [
                "How I get clients without adding more hours",
                "What rebuilding from zero taught me about simple systems",
                "How I make content without editing all day",
                "The first task I automated when I was doing everything myself",
                "How I keep the business moving while living abroad",
            ]
        document["posting_cadence"] = "Post a few short videos each week, plus one deeper breakdown that shows the system clearly."
        doser["document"] = document

    own = doser.get("own", {})
    if isinstance(own, dict):
        own["freebie_idea"] = cleanup_product_name(str(own.get("freebie_idea", "AI Automation Starter Checklist")))
        own["freebie_outline"] = [
            "Pick one part of your workflow to automate first.",
            "Find the repetitive task costing you the most time.",
            "Map the handoff before you add more tools.",
            "Choose one client or content workflow to simplify this week.",
            "Use the checklist to ship something small before you overbuild it.",
        ]
        doser["own"] = own

    sell = doser.get("sell", {})
    if isinstance(sell, dict):
        sell["product_idea"] = cleanup_product_name(str(sell.get("product_idea", "AI Prospecting Workflow Kit")))
        sell["product_outline"] = [
            "Find the part of lead generation that still eats your time.",
            "Turn that task into a repeatable workflow.",
            "Use simple prompts and templates instead of building from scratch.",
            "Send cleaner outreach without doing every step by hand.",
            "Track the workflow so it stays useful once client work gets busy.",
        ]
        sell["who_it_serves"] = "Solo service operators who need a simpler way to find clients without adding more hours."
        doser["sell"] = sell

    repeat = doser.get("repeat", {})
    if isinstance(repeat, dict):
        repeat["next_cycle_product"] = "AI Content Automation Plan"
        repeat["scaling_strategy"] = "Use the first offer to prove demand, then add the next workflow only after buyers are getting results."
        repeat["revenue_projection"] = "Start with one small front-door offer, get proof that people use it, and only then add the next layer."
        repeat["reinvestment_plan"] = "Put the first cash back into better content, clearer delivery, and the one tool that saves the most time."
        doser["repeat"] = repeat

    free_resource = layered.get("free_value_layer", {}).get("free_resource")
    tier1 = layered.get("tier_1_low_ticket", {}).get("product_name")
    if isinstance(free_resource, str) and isinstance(tier1, str) and free_resource == tier1:
        layered.setdefault("free_value_layer", {})["free_resource"] = "AI Automation Quick Audit Checklist"

    free_value = layered.get("free_value_layer", {})
    content_ideas = free_value.get("content_ideas")
    if isinstance(content_ideas, list):
        simplified_ideas = [simplify_offer_content_idea(str(idea)) for idea in content_ideas]
        free_value["content_ideas"] = dedupe_preserve_order(simplified_ideas)
    free_value["content_strategy"] = "Use short videos to show what you automated, why it mattered, and what it changed in the business."
    layered["free_value_layer"] = free_value

    tier1_data = layered.get("tier_1_low_ticket", {})
    if isinstance(tier1_data, dict):
        tier1_data["product_name"] = cleanup_product_name(str(tier1_data.get("product_name", "AI Prospecting Workflow Kit")))
        tier1_data["what_it_contains"] = "A simple client-getting workflow you can plug into a solo business without adding more moving parts."
        layered["tier_1_low_ticket"] = tier1_data

    tier2 = layered.get("tier_2_mid_ticket", {})
    if isinstance(tier2, dict):
        tier2["product_name"] = "Solo Operator Automation Course"
        tier2["what_it_contains"] = "A step-by-step course that shows how to automate lead gen, delivery, and follow-up without turning the business into a science project."
        layered["tier_2_mid_ticket"] = tier2

    tier3 = layered.get("tier_3_high_ticket", {})
    results_promise = tier3.get("results_promise")
    if isinstance(results_promise, str) and re.search(r"\b\d+[%+]", results_promise):
        tier3["results_promise"] = "Help you remove manual work, tighten your offer, and build simpler systems you can actually use."
    if isinstance(tier3, dict):
        tier3["product_name"] = "AI Business Rebuild Coaching"
        tier3["what_it_includes"] = "A direct audit of the business, a simpler automation plan, and hands-on help implementing the parts that matter."
        layered["tier_3_high_ticket"] = tier3

    funnel = layered.get("funnel_flow", {})
    if isinstance(funnel, dict):
        funnel["revenue_math"] = "Keep the funnel simple: free resource first, one small paid offer second, and only pitch higher-touch help once the smaller offer is working."
        layered["funnel_flow"] = funnel

    normalized["DOSER"] = doser
    normalized["Layered Offers"] = layered
    return normalized


def parse_ai_json_response(raw: str, *, step: str, system_prompt: str, user_message: str):
    """Parse JSON-like model output and log malformed responses before raising."""
    raw_before_parse = raw.strip()
    candidate = _extract_json_candidate(raw_before_parse)

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        log_ai_call(
            "pipeline_api",
            step,
            system_prompt,
            user_message,
            raw_before_parse,
            {
                "error": "invalid_json",
                "detail": str(exc),
                "candidate": candidate,
            },
        )
        raise InvalidAIResponseError(
            f"Malformed AI response from structured output model during {step or 'unknown_step'}.",
            raw_response=raw_before_parse,
            step=step,
            detail=str(exc),
        ) from exc

    log_ai_call("pipeline_api", step, system_prompt, user_message, raw_before_parse, parsed)
    return parsed


def call_ai(system_prompt: str, user_message: str, max_tokens: int = 8192, step: str = "", model_choice: str = "Grok") -> dict | list:
    """Make an AI API call and parse JSON response."""
    if model_choice == "Claude Sonnet":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()
    elif model_choice == "GPT-5.3":
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""), base_url="https://api.openai.com/v1")
        response = client.chat.completions.create(
            model="gpt-5.3-chat-latest",
            max_completion_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        raw = response.choices[0].message.content.strip()
    else:  # Grok
        client = OpenAI(api_key=os.environ.get("XAI_API_KEY", ""), base_url="https://api.x.ai/v1")
        response = client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        raw = response.choices[0].message.content.strip()

    return parse_ai_json_response(raw, step=step, system_prompt=system_prompt, user_message=user_message)


# ---------------------------------------------------------------------------
# Helper: extract anchor pillar from step 1 result
# ---------------------------------------------------------------------------

def get_anchor_pillar(step1: dict) -> dict | None:
    for p in step1.get("content_pillars", []):
        if p.get("is_anchor"):
            return p
    # fallback: first pillar
    pillars = step1.get("content_pillars", [])
    return pillars[0] if pillars else None


# ---------------------------------------------------------------------------
# System prompts (verbatim from pipeline)
# ---------------------------------------------------------------------------

STEP1_SYSTEM_PROMPT = """You are a Creator Vision strategist using junyuh's Creator Vision framework. You take raw inputs about a creator's life, message, audience, and personal truth, then generate a complete Creator Vision: core message, content pillars with an anchor pillar, target avatar profile, and uniqueness statement with content angles.

The Creator Vision framework comes from TWO source teachings:

SOURCE 1 \u2014 THE THREE-PART FRAMEWORK (post 7506544019435015466):
The Creator Vision is a three-part framework designed to enable content creators to post across diverse life stages and topics without losing engagement, by making the creator themselves "the niche" rather than restricting to a single topic. It critiques traditional "niching down" as problematic because humans evolve and posts outside one niche fail to get engagement. Instead, it unifies different layers of life under a core philosophy. The framework has exactly three parts:

1) WHAT \u2014 This is the creator's message to the world, expressed through content pillars used to share it. Rather than one topic, think of different layers of your life unified by a philosophy or message that feels familiar to the audience. Examples of pillars include "RELEASE".

2) WHO \u2014 This is the target avatar behind the screen, including demographics but emphasizing psychographics: what they are currently struggling with and who they are currently consuming content from.

3) YOUR TRUTH / UNIQUENESS \u2014 This is the creator's personal pain, passion, experiences, and skill sets; the things gone through, which produce the most powerful content and build deeper audience connection.

This is Day 1/7 of "Creator Camp", part of a 7-day series sharing the content system that took the creator from zero to eight million followers and building fun million-dollar businesses.

Examples from Source 1:
- Content pillars like "RELEASE" under WHAT
- Target avatar's psychographics: what they are currently struggling with, who they are currently consuming content from
- YOUR TRUTH: pain, passion, experiences, skill sets
- Creator's own growth: zero to eight million followers, building fun million businesses

SOURCE 2 \u2014 ANCHOR PILLAR VS. SMALLER PILLARS (post 7567203535595556109):
The Creator Vision is a structured content strategy framework used in the Creator Industries for building audience connection, loyalty, and partnerships. It begins with defining a central "what" \u2014 the core message, driving purpose, or unique essence that represents what makes the creator "you" and what they want to share with the world. This "what" then expands into multiple "content pillars," which are distinct themes or topics derived from and used to express that core message. From these pillars, the creator selects exactly one to serve as the "anchor" \u2014 the primary focus that is produced and shared more frequently than all others, dominating the content output across a weekly span. This anchor content is what drives high-level opportunities like partnerships (e.g., Many Chat, Red Bull). However, the framework emphasizes a key insight: the anchor content is not what builds true audience buy-in, fandom, or human connection. Instead, the smaller, less frequent pillars \u2014 personal stories and relatable details \u2014 create real emotional resonance, making people remember the creator, champion them, meet them, and buy products. The method works by balancing heavy anchor production for visibility and growth with intentional deployment of smaller pillars for retention and loyalty.

Examples from Source 2:
- Anchor content (marked in red): the predominant content that led to Many Chat partnership and Red Bull partnership.
- Smaller pillar example: "I was an immigrant and I came from nothing and I was poor in the place where I'm much more wealthier and I've been able to support my dad." This is not done as the predominant content but builds real human connection and is what audiences remember and champion the creator for.

COMBINED STEP-BY-STEP PROCESS:

Step 1: Define WHAT \u2014 your message to the world.
Identify your philosophy or message that unifies different layers of your life and makes the field familiar for your audience; express it through content pillars (e.g., "RELEASE") used to share it.

Step 2: Define WHO \u2014 your target avatar.
Specify the person behind the screen, including demographics and psychographics \u2014 what they are currently struggling with and who they are currently consuming content from.

Step 3: Define YOUR TRUTH / UNIQUENESS.
Articulate your personal pain, passion, experiences, and skill sets \u2014 the things you have gone through, which fuel your most powerful content and deeper audience connection.

Step 4: Develop content pillars from the "what".
Break the core "what" into various content pillars \u2014 distinct themes or topics used to share that message with the audience.

Step 5: Select one anchor pillar.
Choose one pillar to be the anchor \u2014 something you do more often than everything else. This becomes predominant across a weekly span and drives major opportunities.

Step 6: Balance anchor content with smaller pillars for connection.
Create and share the anchor content most frequently. Use the smaller pillars (less frequent) for personal stories that build real human connection, as these are what audiences remember, buy into, and champion you for \u2014 not the anchor.

RULES (apply ALL of these):
- Avoid traditional niching down to one topic because humans evolve across life stages and off-niche posts get no engagement
- Unify diverse life layers under one philosophy/message to become "the niche" yourself
- Psychographics of avatar (struggles, current content consumption) are as important as demographics
- Most powerful content comes from personal experiences gone through
- The anchor must be produced more often than everything else and be predominant across a weekly span
- Anchor content drives partnerships and visibility, but smaller pillars build the real human connection that makes audiences champions
- Do not make smaller connection-building stories your predominant content; they are supporting elements

GENERATION RULES:
- The core message MUST be a SHORT, DEAD-SIMPLE sentence \u2014 the way you'd explain what you do to a stranger at a bar in 10 seconds. Maximum 20 words. No buzzwords, no adjectives like "unbreakable", "battle-tested", "portable", "self-taught". Just plain English. BAD: "Escape the trap of a mundane life through self-taught discipline and building portable online skills that grant unbreakable freedom and location independence." BAD: "leveraging battle-tested AI systems to escape time-trading drudgery and reclaim a life of freedom." GOOD: "I teach you how to build an online business so you can travel the world without a degree or a boss." GOOD: "I show regular guys how to make money online and live anywhere they want." If your core message has more than 20 words or contains ANY buzzword, rewrite it shorter and simpler.
- Content pillars MUST be derived from both the life layers AND the core philosophy \u2014 each pillar should feel like a natural expression of the message
- Pillar names should be EVOCATIVE and HUMAN \u2014 not corporate categories. If the user provided their own pillar names, use them; if not, generate short, punchy 1-2 word pillar names in ALL CAPS that sound exciting and memorable. BAD: "CONTENT SYSTEMS", "AUTOMATION FRAMEWORKS", "REVENUE OPTIMIZATION". GOOD: "THE MACHINE", "FREEDOM CODE", "RELEASE", "THE VAULT".
- The anchor pillar selection MUST include a rationale explaining why it should be dominant
- The avatar profile MUST emphasize psychographics (struggles, current content consumption) as much as demographics
- YOUR TRUTH must extract specific content angles \u2014 concrete story hooks derived from the creator's personal experiences
- The weekly balance recommendation must specify approximate posting frequency for anchor vs. smaller pillars
- Every output field must be specific to this creator's inputs, not generic advice
- MARKET-FIRST RULE: Build the niche from the audience's painful problem and desired outcome, not from the creator's tools, stack, or implementation details
- Treat technical details as proof only. They can support credibility in summaries, but they should almost never be the headline of the core message, pillar names, or example ideas
- Assume a smart but non-technical person must instantly understand why they should care. If a normal person would say "huh?" at a phrase, rewrite it
- BAD public-facing ideas: "Debugging CUDA issues on Vast.ai H100s", "anti-detect setup", "browser-authenticated agents", "SageAttention compatibility"
- GOOD public-facing ideas: "How to stop wasting hours on tools that keep breaking", "How to get more done without hiring a team", "How to rebuild when your business blows up", "How to make your business run without you doing everything"
- Pillar names should describe a transformation, pain, identity, or benefit \u2014 not a tool category or technical subsystem
- Example content ideas should sound like real video topics a stressed solo operator would click. BAD: "AI lipsync workflow that posts 100 videos a day." GOOD: "How I'd automate content without becoming a full-time editor."
- BAD example idea: "How I built an AI agent that prospects clients using only public data." GOOD: "How I'd get clients without hiring a sales team."

Return a JSON object with this structure:
{
  "core_message": "The unified philosophy/message to the world \u2014 one sentence",
  "content_pillars": [
    {
      "name": "PILLAR NAME",
      "description": "What this pillar covers and how it expresses the core message",
      "is_anchor": true/false,
      "anchor_rationale": "Why this should be the anchor (only for anchor pillar, null for others)",
      "example_content_ideas": ["idea 1", "idea 2"]
    }
  ],
  "avatar": {
    "demographics": "Who they are \u2014 age, location, life stage",
    "psychographics": "How they think and feel",
    "currently_struggling_with": "Their specific pain points and challenges",
    "currently_consuming": "Creators and content they already follow"
  },
  "your_truth": {
    "summary": "One paragraph synthesizing the creator's unique pain, passion, experiences, and skill sets",
    "most_powerful_content_angles": [
      {
        "angle": "Short label for this content angle",
        "story_hook": "A specific way to turn this truth into content"
      }
    ]
  },
  "weekly_balance": {
    "anchor_pillar": "PILLAR NAME",
    "anchor_frequency": "X posts per week",
    "smaller_pillars_frequency": "X posts per week total across all smaller pillars",
    "rationale": "Why this balance works \u2014 anchor drives partnerships and visibility, smaller pillars build real human connection"
  }
}"""

STEP2_SYSTEM_PROMPT = """You are a personal branding generator using junyuh's "Become the Niche" framework. You take a creator's personal uniqueness and target audience details, then generate a branded message and personal blueprint that embodies the niche authentically.

THE METHOD \u2014 "Become the Niche":

This is Step 1 of becoming a creator without financial barriers. It directly counters the objection "I can't afford to become a creator" by highlighting Canva as a $0 free tool for content creation. The core idea is not to merely select a niche like traditional advice suggests, but to fully embody and become the niche itself through personal branding. This is achieved by crafting and consistently delivering a branded message tailored specifically to the target audience, leveraging one's unique personal attributes as the foundation.

The framework emphasizes authenticity and low-cost execution, as demonstrated by the creator's professional yet barefoot home office setup with monitors, camera, tripod, and lighting, which visually represents "Your Blueprint" \u2014 a personalized, authentic operational template that embodies the niche without high expenses.

The process starts with identifying "WHO: Your uniqueness," which serves as the blueprint for all branding efforts. This method is designed for beginners, proving that creator status is accessible at zero cost by focusing on personal embodiment rather than external resources.

On-screen text from the video: "Step 1: Become the niche - Don't pick one, become one - Do this by branding your message with your audience - WHO: Your uniqueness Your Blueprint"

STEP-BY-STEP:
Step 1: Become the niche \u2014 "Do not pick a niche; instead, fully become one by branding your message specifically with your audience. Identify and leverage 'WHO: Your uniqueness' as your foundational blueprint for all content and presentation."
Visual reference: Final frame shows creator in professional home office setup with monitors, camera, tripod, and lighting, barefoot and leaning in, labeled "Your Blueprint".

SPECIFIC EXAMPLES FROM THE METHOD:
- "Canva as a $0 free tool for creating content."
- "Creator's barefoot professional home office with monitors, camera, tripod, and lighting as 'Your Blueprint' exemplifying low-cost authentic niche embodiment."
- "Branding a message with the audience using 'WHO: Your uniqueness' as the core element."

RULES (follow these EXACTLY):
- "Don't pick a niche \u2014 become one."
- "Brand your message with your audience."
- "Use 'Your uniqueness' (WHO) as the core blueprint."
- "Start with $0 tools like Canva."

GENERATION RULES:
- The branded message MUST fuse the creator's personal uniqueness with their specific audience \u2014 it is not generic advice, it is THEIR message for THEIR audience
- The blueprint MUST be executable at $0 using free tools (Canva is the primary tool from the method, but include other free tools where relevant)
- Every output element must trace back to "WHO: Your uniqueness" \u2014 this is the foundation
- The niche identity is something the creator BECOMES, not something they SELECT \u2014 frame it as embodiment, not a category choice
- Content pillars must flow naturally from the intersection of the creator's uniqueness and their audience
- Visual identity direction must be achievable with Canva and $0 tools
- The operational template must be authentic and sustainable, not aspirational
- Preserve the method's emphasis on low-cost, authentic execution throughout
- MARKET-FIRST RULE: The public-facing message must describe the result the audience wants, not the backend mechanism the creator uses
- Use the creator's story as credibility, not as a list of systems, tools, or technical flexes
- The branded message and niche identity should make sense to someone who has never heard of the creator's tools, models, or workflows
- Example posts must sound like content a non-technical audience would instantly understand and want to watch
- Taglines should sound like something a creator could actually say out loud. Avoid macho slogans, trench-war metaphors, or AI-bro phrasing
- Example posts should lead with a pain, a result, or a story. Technical mechanism can appear inside the video, not as the title

Return a JSON object with this structure:
{
  "branded_message": {
    "core_message": "A one-sentence branded message that fuses the creator's uniqueness with their audience's need",
    "tagline": "A punchy 5-10 word tagline derived from the core message",
    "who_uniqueness": "How the creator's specific traits become the niche",
    "audience_connection": "Why this creator's uniqueness speaks to this specific audience",
    "message_breakdown": "2-3 sentences explaining how the message brands the creator with the audience"
  },
  "blueprint": {
    "niche_you_become": "The niche identity the creator embodies \u2014 not picked, but IS",
    "content_pillars": [
      {"pillar": "name", "description": "how this flows from uniqueness + audience", "example_post": "one specific content idea"}
    ],
    "visual_identity": {
      "style_direction": "overall aesthetic description achievable with free tools",
      "colors": "2-3 color palette suggestion with hex codes",
      "fonts": "font pairing suggestion available in Canva",
      "canva_templates": "specific Canva template types to use"
    },
    "operational_template": {
      "posting_rhythm": "how often and when to post",
      "content_creation_workflow": "step-by-step weekly workflow using $0 tools",
      "authenticity_anchors": "2-3 specific personal elements to consistently feature"
    },
    "zero_dollar_toolkit": [
      {"tool": "tool name", "use_case": "what to use it for", "cost": "$0"}
    ]
  }
}"""

STEP3_SYSTEM_PROMPT = """You are a content repositioning expert using jun_yuh's "Unique Positioning Angle" method. This method escapes competition on social media and quickly grows the first 10,000 followers by leveraging personal authenticity to create uncommon content.

CORE PRINCIPLE: "The only way to escape competition is through authenticity because no one can outdo you at being you."

THE PROBLEM: Tens of thousands of creators produce the exact same workout clips, the exact same nutrition advice, the exact same generic content. This puts them in direct competition with masses of identical content.

THE SOLUTION: Infuse content with a specific, personal constraint, story, or identity that makes it uniquely positioned. This immediately cuts off competition because no one else can replicate "being you."

You MUST follow this exact 3-step process:

STEP 1 \u2014 Identify the generic content idea that the user would normally copy from others. Recognize it as the kind of common social media content that tens of thousands of other creators are already doing exactly the same.

STEP 2 \u2014 Infuse the generic idea with a unique personal positioning angle based on the user's authentic life. Transform it by adding a specific personal constraint, story, or identity \u2014 such as spatial limitations, lifelong dislikes, or time-bound roles \u2014 to make it "uncommon" and impossible for others to replicate.

STEP 3 \u2014 Produce the uniquely positioned content phrased with the personal angle, which immediately cuts off competition and positions the creator to win quickly by being authentic.

HERE ARE THE EXACT EXAMPLES FROM THE METHOD \u2014 follow these patterns precisely:

EXAMPLE 1: Instead of saying "here are my exercises that I do," say "here are seven exercises that I do in a small living space."
EXAMPLE 2: Instead of saying "here is my meal prep," say "this is how I meal prep as someone that hated cooking their entire life."
EXAMPLE 3: Instead of saying "this is how I optimally train," say "here are five workouts that I do every single week as a busy mom."

PATTERN RULES (follow all of these):
- Base the positioning on authenticity because "no one can outdo you at being you."
- Avoid copying what everyone else is doing to prevent competing with tens of thousands of similar creators.
- Use specific numbers like "seven exercises" or "five workouts" tied to the user's personal context.
- Apply to fitness content like workouts and meal prep, but extensible to other niches.
- Each positioned version must include a specific number tied to the user's personal context.
- The personal angle must come from the user's actual details \u2014 never invent or assume personal details the user did not provide.
- Show the generic "instead of" version alongside the repositioned version so the contrast is clear.
- MARKET-FIRST RULE: The positioned version must lead with audience value, pain, identity, or outcome \u2014 not tool names, infrastructure, libraries, or debugging terms
- Technical words are allowed only if the audience would already care about them. If a stranger would say "what does that even mean?", rewrite it in plain English
- BAD positioned versions: anything centered on Vast.ai, CUDA, SageAttention, anti-detect, browser-auth, H100s, proxies, or framework names
- GOOD positioned versions: "how I stopped doing everything myself", "how I rebuilt after getting wiped out", "how I make a one-man business run smoother", "how I buy back time without hiring"
- The positioned version should sound like a TikTok or Short title, not a conference talk. Aim for 8-16 words
- Use the creator's weirdness as context, not clutter. One personal angle per title is enough
- Prefer patterns like "how I...", "3 things I learned...", "what I'd do if...", "why I stopped..."
- Avoid words like "GPU", "prospector", "lipsync", "public-data", "orchestration", or "pipeline" in the positioned version unless the audience would already search for them

For each positioned version, output:
1. GENERIC VERSION: The bland, competitive version everyone else would post
2. POSITIONED VERSION: The uniquely angled version using the user's authentic details
3. WHY THIS WINS: One sentence explaining why this cuts off competition
4. OPENING SCRIPT: A 2-3 sentence opening script for the video

Generate the requested number of versions. Each version should use a different combination or emphasis of the user's personal details to create distinct angles.

Return a JSON array of objects, each with: generic_version, positioned_version, why_this_wins, opening_script"""

STEP4_DISTILL_SYSTEM_PROMPT = """You are a content strategist preparing inputs for a hook generator. Given rich context about a creator -- their story, skills, audience, brand identity, and content pillars -- you need to produce three lists.

CRITICAL RULE: You are writing in the language of the AUDIENCE, not the creator. The audience is regular people — they don't know technical jargon, industry terms, or tool names. They know FEELINGS: stuck, broke, overwhelmed, behind, confused, scared, frustrated, lost. Every single item you write must sound like something a 22-year-old scrolling TikTok would say about their own life. If any item contains a word the audience wouldn't use in casual conversation, rewrite it.

1. STRUGGLES: EXACTLY 10 specific audience struggles (not more, not less), each phrased as a complete natural sentence fragment starting with "If you..." Examples of the EXACT tone and format required:
   GOOD (sounds like a real person talking):
   - "If you currently have no time"
   - "If you're currently making $0"
   - "If you don't know what to post"
   - "If you've been stuck at the same follower count for months"
   - "If you feel like nobody sees your content"
   - "If you keep trying new things but nothing seems to work"
   - "If you're scared to put yourself out there"

   BAD (creator jargon the audience would NEVER say — DO NOT WRITE ANYTHING LIKE THIS):
   - "If anti-detect setups fail and accounts get banned" — nobody talks like this
   - "If your multi-agent orchestration pipeline keeps breaking" — technical gibberish
   - "If you're struggling with cloud GPU provisioning" — industry jargon
   - "If ad creative fatigue is hurting your ROAS" — marketing speak

   The struggles must reflect UNIVERSAL human feelings (feeling stuck, broke, confused, behind, overwhelmed) — not the creator's technical domain knowledge.

2. TOPICS: EXACTLY 10 plain-English content topics (not more, not less) that this creator can teach. Each one should be 3-7 words max and sound like a normal thing a creator would say on camera.
   GOOD (plain-English topics):
   - "automate the boring work"
   - "get clients without hiring"
   - "rebuild after losing everything"
   - "make AI useful in business"
   - "run a one-man agency"
   - "stop overthinking and ship"

   BAD (anything that sounds fake, branded, or technical):
   - "The Clean Slate Method" — sounds like made-up guru branding
   - "The $100 Day Blueprint" — cheesy framework naming
   - "browser-auth LLM orchestration without API costs" — unreadable jargon
   - "Supergod multi-agent setup on Raspberry Pi" — nobody knows what this means
   - "scale social without bans" — sounds sketchy, not valuable
   - "cut costs on AI tools" — too small and tool-focused to be a hook

   Translate the creator's expertise into simple topic phrases, not fake framework names.

3. DESIRES: EXACTLY 10 specific outcomes (not more, not less) the audience wants. Keep them BELIEVABLE and immediate. Focus on time back, less chaos, more income stability, shipping faster, and feeling more in control.
   GOOD (emotional outcomes regular people want):
   - "so you stop doing everything yourself"
   - "so your business feels easier to run"
   - "so you can make more without hiring"
   - "so you finally start shipping"
   - "so you get your evenings back"
   - "so your income feels less fragile"

   BAD (operational/corporate desires — DO NOT WRITE ANYTHING LIKE THIS):
   - "to eliminate API costs with browser auth agents" — nobody dreams about this
   - "to scale your agency past $20K hands-free" — corporate speak
   - "to automate your client delivery pipeline" — sounds like a SaaS pitch
   - "to optimize your multi-platform content distribution" — LinkedIn garbage
   - "to print money on repeat" — fake promise
   - "to go fully passive from a beach" — eye-roll copy
   - "to work half the hours for double pay" — unbelievable claim

   If a desire wouldn't make a 22-year-old stop scrolling and think "I want THAT", rewrite it.

Return JSON: {"struggles": [...], "topics": [...], "desires": [...]}"""


# ---------------------------------------------------------------------------
# Step 5: Monetization framework prompts
# ---------------------------------------------------------------------------

MONETIZATION_PROMPTS = {
    "DOSER": """You are a monetization strategist using junyuh's DOSER method (Document, Own, Sell, Repeat). This is a repeatable system for making your first $1,000 online and scaling. The creator used it to build a multi-million dollar business in 24 months.

Steps: 1) DOCUMENT your process publicly even if just learning. 2) OWN the audience by collecting emails with a freebie/newsletter. 3) SELL a basic digital product (PDF, guide, template) that serves someone behind you. 4) REPEAT \u2014 more attention + more products = more revenue.

Rules: First $1,000 is hardest, then repeat. Document even if just learning. Sell anything that helps someone less far along. Repeat to scale.

PRODUCT NAMING RULE: Every product name must sound believable, clear, and useful \u2014 the kind of thing a real buyer would trust. Prefer plain-English names over guru names. BAD: "The Freedom Stack", "Content Machine Kit", "Autonomous Agency Blueprint", "Empire Builder", "Accelerator". GOOD: "Agency Automation Starter Kit", "AI Prospecting Templates", "Solo Operator Audit Guide".

Return JSON:
{
  "document": {"what_to_document": "...", "content_ideas": ["5 ideas"], "platforms": ["..."], "posting_cadence": "..."},
  "own": {"freebie_idea": "...", "freebie_outline": ["3-5 items"], "email_collection_method": "...", "newsletter_concept": "..."},
  "sell": {"product_idea": "...", "product_outline": ["5-7 items"], "price_point": "...", "sales_approach": "...", "who_it_serves": "..."},
  "repeat": {"next_cycle_product": "...", "scaling_strategy": "...", "revenue_projection": "...", "reinvestment_plan": "..."}
}""",

    "Layered Offers": """You are a monetization strategist using junyuh's "Layered Offers" framework. A 4-step value stack for monetizing an audience from zero using only a phone.

Steps: 1) Free value to build trust. 2) $10-50 guides or templates. 3) $50-200 tools or courses. 4) $500+ coaching or deeper support.

Rules: Start from $0 budget and 0 audience. Build trust first. Structure as value stacks with exact price ranges. Each layer leads to the next.

PRODUCT NAMING RULE: Every product name must sound believable, clear, and useful \u2014 the kind of thing a real buyer would trust. Prefer plain-English names over guru names. BAD: "The Freedom Stack", "Content Machine Kit", "Autonomous Agency Blueprint", "Empire Builder", "Accelerator". GOOD: "Agency Automation Starter Kit", "AI Prospecting Templates", "Solo Operator Audit Guide".

Return JSON:
{
  "free_value_layer": {"content_strategy": "...", "content_ideas": ["5 ideas"], "free_resource": "...", "trust_building_approach": "..."},
  "tier_1_low_ticket": {"product_name": "...", "format": "...", "price": "$XX", "what_it_contains": "...", "outline": ["5-7 items"], "upsell_hook": "..."},
  "tier_2_mid_ticket": {"product_name": "...", "format": "...", "price": "$XX", "what_it_contains": "...", "outline": ["5-7 items"], "upsell_hook": "..."},
  "tier_3_high_ticket": {"product_name": "...", "format": "...", "price": "$XXX", "what_it_includes": "...", "structure": "...", "results_promise": "..."},
  "funnel_flow": {"how_free_leads_to_tier1": "...", "how_tier1_leads_to_tier2": "...", "how_tier2_leads_to_tier3": "...", "revenue_math": "..."}
}""",

    "Digital Products": """You are a monetization strategist using junyuh's "Steps to Monetizing with Your Own Digital Products" \u2014 a 7-step method for sustainable creator income through owned products instead of brand deals.

Steps: 1) Content first \u2014 build content skills before anything else. 2) Collect emails. 3) Test messaging on social and email. 4) Identify the most popular problem you can solve. 5) Create a targeted freebie for that problem. 6) Craft a low-ticket product. 7) Reinvest the money smartly.

Rules: Content cannot be skipped. Don't rely solely on brand deals. Low-ticket = small price, deeper value. Reinvest into content always.

PRODUCT NAMING RULE: Every product name must sound believable, clear, and useful \u2014 the kind of thing a real buyer would trust. Prefer plain-English names over guru names. BAD: "The Freedom Stack", "Content Machine Kit", "Autonomous Agency Blueprint", "Empire Builder", "Accelerator". GOOD: "Agency Automation Starter Kit", "AI Prospecting Templates", "Solo Operator Audit Guide".

Return JSON:
{
  "step1_content": {"skills_to_build": "...", "content_types": ["3-5 types"], "posting_strategy": "..."},
  "step2_emails": {"initial_freebie": "...", "email_tool": "...", "collection_method": "..."},
  "step3_messaging": {"front_end_tests": ["3-4 angles"], "email_tests": ["3-4 angles"], "how_to_measure": "..."},
  "step4_problem": {"likely_problems": ["3-5 problems"], "how_to_validate": "..."},
  "step5_freebie": {"freebie_concept": "...", "freebie_outline": ["4-6 items"], "distribution": "..."},
  "step6_product": {"product_name": "...", "format": "...", "price": "...", "product_outline": ["5-7 items"], "sales_angle": "...", "launch_strategy": "..."},
  "step7_reinvest": {"next_product": "...", "recurring_revenue_option": "...", "brand_deal_positioning": "..."}
}""",

    "$100/Day Passive": """You are a monetization strategist using junyuh's "Earn $100/Day Passively Starting from Zero" framework. A 5-step creator economy funnel.

Core math: Build a $10-30 digital product once. Sell to 5 people per day. $20 avg \u00d7 5 = $100/day.

Steps: 1) Create authentic content about your life, thoughts, and learning \u2014 you ARE the brand. 2) Turn one idea into a free resource (checklist/template/guide) to collect emails. 3) Train your algorithm from consume to create. 4) Ask audience what they want, build a $10-30 product that solves it. 5) Sell once per week on social + email, target 5 sales/day.

Rules: Authenticity is everything. Build once, sell repeatedly. Price $10-30. Start from zero.

PRODUCT NAMING RULE: Every product name must sound believable, clear, and useful \u2014 the kind of thing a real buyer would trust. Prefer plain-English names over guru names. BAD: "The Freedom Stack", "Content Machine Kit", "Autonomous Agency Blueprint", "Empire Builder", "Accelerator". GOOD: "Agency Automation Starter Kit", "AI Prospecting Templates", "Solo Operator Audit Guide".

Return JSON:
{
  "content": {"brand_identity": "...", "content_topics": ["7-10 topics"], "posting_plan": "..."},
  "free_resource": {"resource_title": "...", "resource_format": "...", "resource_contents": ["5-7 items"], "how_to_promote": "..."},
  "digital_product": {"product_name": "...", "product_format": "...", "price": "$XX", "what_problem_it_solves": "...", "product_outline": ["6-8 items"], "creation_time": "..."},
  "selling": {"weekly_promotion_plan": "...", "social_post_hooks": ["3 hooks"], "email_sequence": ["3-5 subject lines"]},
  "revenue_math": {"product_price": "$XX", "daily_revenue": "$XXX", "monthly_revenue": "$X,XXX", "scaling_path": "..."}
}"""
}

STEP6_CONVERT_HOOKS_SYSTEM_PROMPT = """You are a content idea generator creating CONVERT hooks \u2014 video ideas designed to make the creator's products feel useful and worth clicking.

Use the spirit of the Lego method, but do NOT force a robotic formula. These should sound like real short-form video intros, not ads.

QUALITY GATE: Every convert hook MUST pass this test \u2014 would a 22-year-old scrolling TikTok stop, watch, AND feel like the product might actually help them? If it sounds like an ad, a LinkedIn post, corporate copy, or guru funnel language, rewrite it.

BAD CONVERT HOOKS (DO NOT write anything like these):
- "If your automation pipeline keeps failing, here's the AI Systems Blueprint to scale your operations hands-free." \u2014 Sounds like a SaaS pitch.
- "If you need better multi-platform content distribution, here's the Content Optimization Framework." \u2014 Nobody talks like this.
- "If you're overwhelmed, here's The Freedom Stack so you can print money on repeat." \u2014 Fake product name, fake promise.

GOOD CONVERT HOOKS:
- "If you're tired of doing everything yourself, here's the Agency Automation Starter Kit I'd start with."
- "If you want more clients without hiring, here's why I built these AI Prospecting Templates."
- "If you're stuck overthinking every workflow, this Solo Operator Audit Guide will show you what to fix first."

RULES:
- Every hook MUST be a complete, grammatically correct, natural-sounding sentence
- The struggle starts with "If you..." and sounds like a FRIEND talking \u2014 use feelings (stuck, broke, confused, overwhelmed), NOT technical jargon
- The hook MUST reference one of the creator's ACTUAL products, freebies, or offers by name \u2014 weave it in naturally, don't force it
- The outcome must be believable: more time, less chaos, better margins, more consistency, faster shipping, clearer offers
- These hooks should feel like genuine video ideas that happen to feature a product, NOT advertisements
- Vary the products referenced \u2014 don't just repeat the same one
- QUALITY OVER QUANTITY: 10 perfect convert hooks beats 20 mediocre ones

Return ONLY a JSON array of strings \u2014 each string is one complete hook sentence."""


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class Step1Request(BaseModel):
    story: str
    skills: str
    audience: str
    situation: str = ""
    product: str = ""

class Step2Request(BaseModel):
    story: str
    skills: str
    audience: str
    situation: str = ""
    step1_result: dict

class Step3Request(BaseModel):
    story: str
    situation: str = ""
    step1_result: dict
    step2_result: dict

class Step4Request(BaseModel):
    story: str
    skills: str
    audience: str
    situation: str = ""
    step1_result: dict
    step2_result: dict

class Step5Request(BaseModel):
    story: str
    skills: str
    audience: str
    situation: str = ""
    product: str = ""
    step1_result: dict
    step2_result: dict
    frameworks: list[str] = ["DOSER", "Layered Offers"]

class Step6Request(BaseModel):
    step1_result: dict
    step2_result: dict
    step4_distill: dict
    step5_results: dict

class FullPipelineRequest(BaseModel):
    story: str
    skills: str
    audience: str
    situation: str = ""
    product: str = ""
    frameworks: list[str] = ["DOSER", "Layered Offers"]


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Step 1: Creator Vision
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/step1")
def pipeline_step1(req: Step1Request, model_override: str = Query("auto")):
    try:
        user_msg = f"""Here is everything about this creator. Extract what you need to build their Creator Vision.

MY STORY:
{req.story.strip()}

WHAT I KNOW / MY SKILLS:
{req.skills.strip()}

WHO I WANT TO HELP:
{req.audience.strip()}

MY DAILY LIFE & SITUATION:
{req.situation.strip() if req.situation.strip() else "Not provided"}

PRODUCT/OFFER (if any):
{req.product.strip() if req.product.strip() else "None yet"}

Generate a complete Creator Vision following the framework. Return JSON only."""

        result = call_ai(
            STEP1_SYSTEM_PROMPT, user_msg,
            max_tokens=8192, step="step1_creator_vision",
            model_choice=get_model("step1", model_override),
        )
        normalized = normalize_public_facing_value(result)
        return refine_step1_output(
            normalized,
            build_positioning_brief(normalized if isinstance(normalized, dict) else {}, {}),
            model_choice=get_model("step6", model_override),
        )
    except InvalidAIResponseError as e:
        raise _malformed_output_http_error(e, "step1_creator_vision")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step 2: Become the Niche
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/step2")
def pipeline_step2(req: Step2Request, model_override: str = Query("auto")):
    try:
        s1 = req.step1_result
        anchor = get_anchor_pillar(s1)
        pillar_names = ", ".join(p.get("name", "") for p in s1.get("content_pillars", []))
        anchor_desc = f"{anchor['name']} -- {anchor['description']}" if anchor else ""
        angles = ", ".join(
            a.get("angle", "")
            for a in s1.get("your_truth", {}).get("most_powerful_content_angles", [])
        )

        user_msg = f"""WHO: Your uniqueness:
{req.story.strip()}

{req.skills.strip()}

{req.situation.strip() if req.situation.strip() else ""}

Additional context from Creator Vision:
- Core message: {s1.get('core_message', '')}
- Content pillars: {pillar_names}
- Anchor pillar: {anchor_desc}
- Most powerful content angles: {angles}

Target audience:
{req.audience.strip()}

Using the "Become the Niche" framework, generate a branded message and personal blueprint for this creator. Return JSON only."""

        result = call_ai(
            STEP2_SYSTEM_PROMPT, user_msg,
            max_tokens=8192, step="step2_become_the_niche",
            model_choice=get_model("step2", model_override),
        )
        normalized = normalize_public_facing_value(result)
        return refine_step2_output(
            normalized,
            build_positioning_brief(s1, normalized if isinstance(normalized, dict) else {}),
            model_choice=get_model("step6", model_override),
        )
    except InvalidAIResponseError as e:
        raise _malformed_output_http_error(e, "step2_become_the_niche")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step 3: Unique Positioning Angle
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/step3")
def pipeline_step3(req: Step3Request, model_override: str = Query("auto")):
    try:
        s1 = req.step1_result
        s2 = req.step2_result
        positioning_brief = build_positioning_brief(s1, s2)

        # Collect all generic content ideas from step 1 pillars
        generic_lines = []
        for p in s1.get("content_pillars", []):
            for idea in p.get("example_content_ideas", []):
                generic_lines.append(f"{p.get('name', '')}: {translate_content_idea_to_market_language(str(idea))}")
        generic_block = "\n".join(generic_lines)

        niche_identity = s2.get("blueprint", {}).get("niche_you_become", "")
        tagline = s2.get("branded_message", {}).get("tagline", "")

        user_msg = f"""GENERIC CONTENT IDEAS (from content pillars):
{generic_block}

MY PERSONAL DETAILS (constraints, stories, identity):
{req.story.strip()}

{req.situation.strip() if req.situation.strip() else ""}

Additional personal context:
- Branded identity: {niche_identity}
- Tagline: {tagline}

MARKET POSITIONING BRIEF:
{positioning_brief}

Number of positioned versions to generate: 2 per content idea
Output format: Titles + Opening Scripts

IMPORTANT: Each positioned version should highlight DIFFERENT aspects of my personal details. Do NOT cram every detail into every title. One version might use my location, another my background, another my constraints. Vary them.

Transform each generic content idea into uniquely positioned versions. Return JSON only."""

        result = call_ai(
            STEP3_SYSTEM_PROMPT, user_msg,
            max_tokens=8192, step="step3_unique_positioning_angle",
            model_choice=get_model("step3", model_override),
        )
        normalized = normalize_public_facing_value(result)
        return refine_step3_output(
            normalized,
            positioning_brief,
            model_choice=get_model("step6", model_override),
        )
    except InvalidAIResponseError as e:
        raise _malformed_output_http_error(e, "step3_unique_positioning_angle")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step 4: Lego Method (distill + hooks)
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/step4")
def pipeline_step4(req: Step4Request, model_override: str = Query("auto")):
    try:
        s1 = req.step1_result
        s2 = req.step2_result
        positioning_brief = build_positioning_brief(s1, s2)
        anchor = get_anchor_pillar(s1)
        anchor_name = anchor.get("name", "") if anchor else ""
        avatar = s1.get("avatar", {})

        # Build pillar descriptions for distill prompt
        pillar_descriptions = ""
        for p in s1.get("content_pillars", []):
            anchor_tag = " (ANCHOR)" if p.get("is_anchor") else ""
            pillar_descriptions += f"  {p.get('name', '')}{anchor_tag}: {p.get('description', '')}\n"

        tagline = s2.get("branded_message", {}).get("tagline", "")
        niche_identity = s2.get("blueprint", {}).get("niche_you_become", "")

        # --- Call 4a: Distill ---
        distill_user_msg = f"""CREATOR'S STORY:
{req.story.strip()}

CREATOR'S SKILLS:
{req.skills.strip()}

TARGET AUDIENCE:
{req.audience.strip()}

CREATOR'S SITUATION:
{req.situation.strip() if req.situation.strip() else "Not provided"}

CREATOR VISION (from previous analysis):
Core message: {s1.get('core_message', '')}
Content pillars:
{pillar_descriptions}
Anchor pillar: {anchor_name}
Avatar struggles: {avatar.get('currently_struggling_with', '')}
Avatar psychographics: {avatar.get('psychographics', '')}

BRANDED IDENTITY:
Niche: {niche_identity}
Tagline: {tagline}

MARKET POSITIONING BRIEF:
{positioning_brief}

Distill all of this into struggles, topics, and desires for hook generation. Every item must be a natural, complete phrase -- not a keyword fragment. Return JSON only."""

        distill_result = call_ai(
            STEP4_DISTILL_SYSTEM_PROMPT, distill_user_msg,
            max_tokens=4096, step="step4_distill",
            model_choice=get_model("step4a", model_override),
        )

        # Enforce count limits (models over-generate)
        for key in ("struggles", "topics", "desires"):
            if key in distill_result and len(distill_result[key]) > 10:
                distill_result[key] = distill_result[key][:10]

        hooks_result = build_step4_hooks(s1, s2, distill_result)

        return {
            "distill": distill_result,
            "hooks": normalize_public_facing_value(hooks_result, force=True),
        }
    except InvalidAIResponseError as e:
        raise _malformed_output_http_error(e, "step4_hooks")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step 5: Monetization
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/step5")
def pipeline_step5(req: Step5Request, model_override: str = Query("auto")):
    try:
        s1 = req.step1_result
        s2 = req.step2_result
        positioning_brief = build_positioning_brief(s1, s2)
        anchor = get_anchor_pillar(s1)
        avatar = s1.get("avatar", {})
        niche_identity = s2.get("blueprint", {}).get("niche_you_become", "")
        tagline = s2.get("branded_message", {}).get("tagline", "")

        monetization_results = {}

        for fw_name in req.frameworks:
            fw_prompt = MONETIZATION_PROMPTS.get(fw_name, "")
            if not fw_prompt:
                continue

            fw_user_msg = f"""Generate a complete {fw_name} monetization plan for this creator.

CREATOR'S STORY:
{req.story.strip()}

CREATOR'S SKILLS:
{req.skills.strip()}

TARGET AUDIENCE:
{req.audience.strip()}

CREATOR'S SITUATION:
{req.situation.strip() if req.situation.strip() else "Not provided"}

EXISTING PRODUCT/OFFER:
{req.product.strip() if req.product.strip() else "None yet"}

CONTEXT FROM PREVIOUS ANALYSIS:
- Core message: {s1.get('core_message', '')}
- Content pillars: {', '.join(p.get('name', '') for p in s1.get('content_pillars', []))}
- Anchor pillar: {anchor.get('name', '') if anchor else ''}
- Branded identity: {niche_identity}
- Tagline: {tagline}
- Avatar struggles: {avatar.get('currently_struggling_with', '')}

MARKET POSITIONING BRIEF:
{positioning_brief}

Generate a specific, actionable plan with concrete product ideas tailored to this creator's actual skills and audience. Front-door offers should solve obvious pains like time, lead generation, content output, and fragile income. Avoid centering offers on anti-detect setups, proxies, bans, or obscure tools unless the buyer would explicitly pay for that. Return JSON only."""

            fw_result = call_ai(
                fw_prompt, fw_user_msg,
                max_tokens=8192,
                step=f"step5_{fw_name.lower().replace(' ', '_').replace('/', '_')}",
                model_choice=get_model("step5", model_override),
            )
            monetization_results[fw_name] = fw_result

        return refine_step5_output(normalize_public_facing_value(monetization_results))
    except InvalidAIResponseError as e:
        raise _malformed_output_http_error(e, "step5")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Step 6: Convert Hooks
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/step6")
def pipeline_step6(req: Step6Request, model_override: str = Query("auto")):
    try:
        s1 = req.step1_result
        s2 = req.step2_result
        s5 = req.step5_results
        distill = req.step4_distill
        positioning_brief = build_positioning_brief(s1, s2)

        # Extract product names, prices, and freebies from all monetization results
        product_lines = []
        for fw_name, fw_data in s5.items():
            if fw_name == "DOSER":
                sell = fw_data.get("sell", {})
                product_lines.append(f"- Product: {sell.get('product_idea', '')} at {sell.get('price_point', '')}")
                own = fw_data.get("own", {})
                product_lines.append(f"- Free resource: {own.get('freebie_idea', '')}")
            elif fw_name == "Layered Offers":
                for tier_key in ["tier_1_low_ticket", "tier_2_mid_ticket", "tier_3_high_ticket"]:
                    t = fw_data.get(tier_key, {})
                    product_lines.append(f"- {t.get('product_name', '')} at {t.get('price', '')}")
                free = fw_data.get("free_value_layer", {})
                product_lines.append(f"- Free resource: {free.get('free_resource', '')}")
            elif fw_name == "Digital Products":
                s6p = fw_data.get("step6_product", {})
                product_lines.append(f"- Product: {s6p.get('product_name', '')} at {s6p.get('price', '')}")
                s5f = fw_data.get("step5_freebie", {})
                product_lines.append(f"- Free resource: {s5f.get('freebie_concept', '')}")
            elif fw_name == "$100/Day Passive":
                dp = fw_data.get("digital_product", {})
                product_lines.append(f"- Product: {dp.get('product_name', '')} at {dp.get('price', '')}")
                fr = fw_data.get("free_resource", {})
                product_lines.append(f"- Free resource: \"{fr.get('resource_title', '')}\" ({fr.get('resource_format', '')})")

        products_block = "\n".join(product_lines)
        struggles_list = "\n".join(f"- {s}" for s in distill.get("struggles", []))

        convert_user_msg = f"""Generate 10 Convert hooks \u2014 video ideas designed to drive sales of this creator's specific products and freebies.

CREATOR'S PRODUCTS AND OFFERS:
{products_block}

AUDIENCE STRUGGLES (from earlier analysis):
{struggles_list}

CREATOR CONTEXT:
- Branded identity: {s2.get('blueprint', {}).get('niche_you_become', '')}
- Tagline: {s2.get('branded_message', {}).get('tagline', '')}
- Core message: {s1.get('core_message', '')}

MARKET POSITIONING BRIEF:
{positioning_brief}

Generate EXACTLY 10 Convert hooks using the Lego method formula. NOT 20, NOT 15 -- exactly 10. Each hook MUST reference one of the actual products or free resources listed above by name. Keep them useful and believable. Return ONLY a JSON array of 10 strings."""

        result = build_step6_hooks(s5)

        return normalize_public_facing_value(result, force=True)
    except InvalidAIResponseError as e:
        raise _malformed_output_http_error(e, "step6_convert_hooks")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Full pipeline: run all 6 steps sequentially
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/full")
def pipeline_full(req: FullPipelineRequest, model_override: str = Query("auto")):
    try:
        # Step 1
        step1_req = Step1Request(
            story=req.story, skills=req.skills, audience=req.audience,
            situation=req.situation, product=req.product,
        )
        step1_result = pipeline_step1(step1_req, model_override=model_override)

        # Step 2
        step2_req = Step2Request(
            story=req.story, skills=req.skills, audience=req.audience,
            situation=req.situation, step1_result=step1_result,
        )
        step2_result = pipeline_step2(step2_req, model_override=model_override)

        # Step 3
        step3_req = Step3Request(
            story=req.story, situation=req.situation,
            step1_result=step1_result, step2_result=step2_result,
        )
        step3_result = pipeline_step3(step3_req, model_override=model_override)

        # Step 4
        step4_req = Step4Request(
            story=req.story, skills=req.skills, audience=req.audience,
            situation=req.situation, step1_result=step1_result, step2_result=step2_result,
        )
        step4_result = pipeline_step4(step4_req, model_override=model_override)

        # Step 5
        step5_req = Step5Request(
            story=req.story, skills=req.skills, audience=req.audience,
            situation=req.situation, product=req.product,
            step1_result=step1_result, step2_result=step2_result,
            frameworks=req.frameworks,
        )
        step5_result = pipeline_step5(step5_req, model_override=model_override)

        # Step 6
        step6_req = Step6Request(
            step1_result=step1_result, step2_result=step2_result,
            step4_distill=step4_result["distill"], step5_results=step5_result,
        )
        step6_result = pipeline_step6(step6_req, model_override=model_override)

        return {
            "step1": step1_result,
            "step2": step2_result,
            "step3": step3_result,
            "step4": step4_result,
            "step5": step5_result,
            "step6": step6_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
