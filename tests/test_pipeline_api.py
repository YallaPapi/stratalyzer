import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api import main


def _mock_openai_response(content: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


class _FakeOpenAIClient:
    def __init__(self, content: str):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: _mock_openai_response(content),
            )
        )


def test_call_ai_extracts_json_from_wrapped_text(monkeypatch):
    monkeypatch.setattr(
        main,
        "OpenAI",
        lambda **kwargs: _FakeOpenAIClient(
            'Here you go:\n```json\n{"hooks": ["one", "two"]}\n```\nShip it.'
        ),
    )

    result = main.call_ai("system", "user", step="step4_hooks", model_choice="Grok")

    assert result == {"hooks": ["one", "two"]}


def test_call_ai_extracts_array_payload_before_inner_objects(monkeypatch):
    monkeypatch.setattr(
        main,
        "OpenAI",
        lambda **kwargs: _FakeOpenAIClient(
            'Sure:\n[\n  {"generic_version":"a","positioned_version":"b"}\n]\nDone.'
        ),
    )

    result = main.call_ai("system", "user", step="step3_unique_positioning_angle", model_choice="Grok")

    assert result == [{"generic_version": "a", "positioned_version": "b"}]


def test_call_ai_logs_invalid_json_before_raising(monkeypatch):
    logged_calls = []

    monkeypatch.setattr(
        main,
        "OpenAI",
        lambda **kwargs: _FakeOpenAIClient('oops this is not json at all'),
    )
    monkeypatch.setattr(main, "log_ai_call", lambda *args: logged_calls.append(args))

    with pytest.raises(main.InvalidAIResponseError) as exc:
        main.call_ai("system", "user", step="step4_hooks", model_choice="Grok")

    assert "Malformed AI response" in str(exc.value)
    assert logged_calls, "expected invalid payload to be logged"
    assert logged_calls[0][4] == 'oops this is not json at all'
    assert logged_calls[0][5]["error"] == "invalid_json"
    assert logged_calls[0][5]["detail"]


def test_normalize_public_facing_text_rewrites_technical_terms():
    text = (
        "Debugging CUDA issues on Vast.ai H100s with SageAttention and anti-detect browser auth "
        "for my Supergod system."
    )

    normalized = main.normalize_public_facing_text(text)

    assert "CUDA" not in normalized
    assert "Vast.ai" not in normalized
    assert "H100" not in normalized
    assert "SageAttention" not in normalized
    assert "anti-detect" not in normalized.lower()
    assert "browser auth" not in normalized.lower()
    assert "Supergod" not in normalized
    assert "AI system" in normalized or "automation" in normalized


def test_normalize_public_facing_value_recurses_through_structured_output():
    payload = [
        {
            "positioned_version": "Supergod on Raspberry Pi with Vast.ai backups",
            "opening_script": "I fixed CUDA issues and SageAttention crashes at 2AM.",
        }
    ]

    normalized = main.normalize_public_facing_value(payload)

    assert "Supergod" not in normalized[0]["positioned_version"]
    assert "Raspberry Pi" not in normalized[0]["positioned_version"]
    assert "Vast.ai" not in normalized[0]["positioned_version"]
    assert "CUDA" not in normalized[0]["opening_script"]


def test_normalize_public_facing_text_removes_fake_framework_names():
    text = (
        "If you've tried AI tools but they break your workflow, here's the Browser Agent Freedom System "
        "and the 5K Hour Killer Pipeline to fix it."
    )

    normalized = main.normalize_public_facing_text(text)

    assert "Browser Agent Freedom System" not in normalized
    assert "5K Hour Killer Pipeline" not in normalized
    assert "AI workflow" in normalized or "buy back your time" in normalized


def test_normalize_public_facing_text_cools_cartoon_promises():
    text = (
        "If VAs keep messing up, here's your VA Replacement Automation Kit to fire your VAs and keep all the profits. "
        "It prints money on repeat, scales forever, and helps you earn $20K passive from Thailand beaches."
    )

    normalized = main.normalize_public_facing_text(text)

    assert "fire your VAs" not in normalized
    assert "keep all the profits" not in normalized
    assert "prints money on repeat" not in normalized
    assert "forever" not in normalized
    assert "$20K passive" not in normalized


def test_normalize_public_facing_text_cools_hype_outcomes_and_offer_names():
    text = (
        "Work half the hours for double pay with this AI Automation Empire Builder Accelerator. "
        "It helps you get beach days back and ship systems that make money."
    )

    normalized = main.normalize_public_facing_text(text)

    assert "double pay" not in normalized
    assert "Empire Builder" not in normalized
    assert "Accelerator" not in normalized
    assert "beach days" not in normalized
    assert "make money" in normalized or "income" in normalized


def test_build_positioning_brief_keeps_market_angle_front_and_center():
    step1 = {
        "core_message": "I show solo entrepreneurs how to automate their businesses with AI so they work less and live more.",
        "avatar": {
            "demographics": "Solo entrepreneurs and small agency owners.",
            "currently_struggling_with": "Doing everything themselves, capped by time, and unsure how to use AI in real work.",
        },
        "your_truth": {
            "summary": "Built real systems after a partnership blow-up and now shows what actually works."
        },
    }
    step2 = {
        "branded_message": {
            "tagline": "AI automation from Thailand's trenches."
        }
    }

    brief = main.build_positioning_brief(step1, step2)

    assert "buy back time" in brief.lower() or "work less" in brief.lower()
    assert "get clients without hiring" in brief.lower()
    assert "gpu" not in brief.lower()
    assert "anti-detect" not in brief.lower()


def test_normalize_public_facing_text_keeps_autopilot_rewrites_grammatical():
    text = "This toolkit helps you get leads on autopilot."

    normalized = main.normalize_public_facing_text(text)

    assert "on with less manual work" not in normalized
    assert "with less manual work" in normalized or "without doing it all yourself" in normalized


def test_normalize_public_facing_text_removes_sleep_and_beach_cliches():
    text = "Build AI that finds clients while you sleep from a Thailand beach with bulletproof workflows."

    normalized = main.normalize_public_facing_text(text)

    assert "while you sleep" not in normalized
    assert "Thailand beach" not in normalized
    assert "bulletproof" not in normalized.lower()


def test_find_quality_issues_flags_resume_style_creator_slop():
    issues = main.find_quality_issues(
        "3 ways I prospect clients from Thailand without VAs or reps",
        kind="title",
    )

    assert issues
    assert any("thailand" in issue.lower() or "vas" in issue.lower() or "prospect" in issue.lower() for issue in issues)


def test_find_quality_issues_allows_plain_spoken_hook():
    issues = main.find_quality_issues(
        "If you're overwhelmed running everything solo, here's how I'd get your evenings back first.",
        kind="hook",
    )

    assert issues == []


def test_find_quality_issues_flags_more_hidden_creator_slop():
    title_issues = main.find_quality_issues(
        "Killed API costs with agents after quitting OnlyFans agency life",
        kind="title",
    )
    hook_issues = main.find_quality_issues(
        "These prospecting templates changed that for me overnight.",
        kind="hook",
    )

    assert title_issues
    assert hook_issues


def test_find_quality_issues_flags_empty_salesy_convert_phrases():
    issues = main.find_quality_issues(
        "This $1,497 coaching gave me the push to finally get solo freedom in Thailand.",
        kind="hook",
    )

    assert issues


def test_translate_content_idea_to_market_language():
    lead_idea = main.translate_content_idea_to_market_language(
        "How I built an AI agent that prospects clients using only public data"
    )
    video_idea = main.translate_content_idea_to_market_language(
        "AI video pipeline that posts daily without me"
    )

    assert "clients" in lead_idea.lower()
    assert "hiring" in lead_idea.lower() or "sales" in lead_idea.lower()
    assert "content" in video_idea.lower() or "videos" in video_idea.lower()
    assert "editing" in video_idea.lower() or "posting" in video_idea.lower()


def test_cleanup_product_name_title_cases_buyer_facing_names():
    cleaned = main.cleanup_product_name("AI Business Rebuild coaching")

    assert cleaned == "AI Business Rebuild Coaching"


def test_cleanup_product_name_simplifies_overwritten_course_titles():
    cleaned = main.cleanup_product_name(
        "Autonomous Agency Prospecting System: Templates and Blueprints to Generate 50 Leads/Week with AI"
    )

    assert cleaned == "AI Prospecting Workflow Kit"


def test_find_quality_issues_flags_branding_cosplay_language():
    issues = main.find_quality_issues(
        "From Thailand's beaches, I show battle-tested solo entrepreneurs how to build AI automation that replaces their grind.",
        kind="brand",
    )

    assert issues


def test_refine_step2_output_rewrites_branding_fields(monkeypatch):
    monkeypatch.setattr(
        main,
        "call_ai",
        lambda *args, **kwargs: [
            "I show solo entrepreneurs how to automate the boring parts of work so they get time back.",
            "Automate the work, keep your life.",
        ],
    )

    result = {
        "branded_message": {
            "core_message": "From Thailand's beaches, I show battle-tested solo entrepreneurs how to build AI automation that replaces their grind.",
            "tagline": "Automate the grind, live the nomad life.",
        },
        "blueprint": {"niche_you_become": "The Patong AI Automator"},
    }

    refined = main.refine_step2_output(result, "brief", model_choice="GPT-5.3")

    assert refined["branded_message"]["core_message"] == "I show solo entrepreneurs how to automate the boring parts of work so they get time back."
    assert refined["branded_message"]["tagline"] == "Automate the work, keep your life."


def test_refine_step1_output_translates_seed_ideas_and_truth(monkeypatch):
    monkeypatch.setattr(
        main,
        "call_ai",
        lambda *args, **kwargs: [
            "I rebuilt after losing everything and now show solo operators what to automate first."
        ],
    )

    result = {
        "core_message": "I show solo entrepreneurs how to automate their business with AI so they work less and live more.",
        "content_pillars": [
            {
                "name": "AI BUILDS",
                "description": "Hands-on breakdowns of building real AI automation systems.",
                "example_content_ideas": ["How I built an AI agent that prospects clients using only public data"],
            }
        ],
        "your_truth": {
            "summary": "Built AI system multi-agents on cheap local device via low-cost to kill API costs."
        },
    }

    refined = main.refine_step1_output(result, "brief", model_choice="GPT-5.3")

    assert refined["content_pillars"][0]["example_content_ideas"][0] == "how I get clients without hiring a sales team"
    assert refined["your_truth"]["summary"] == "I rebuilt after losing everything and now show solo operators what to automate first."


def test_refine_step1_output_dedupes_repeated_seed_ideas():
    result = {
        "content_pillars": [
            {
                "name": "RELEASE",
                "example_content_ideas": [
                    "AI lipsync workflow that posts 50 videos a day",
                    "Generate 100 hooks in 10 minutes with this agent",
                    "My full pipeline for Reels that run without me",
                ],
            }
        ],
        "your_truth": {},
    }

    refined = main.refine_step1_output(result, "brief", model_choice="GPT-5.3")

    assert len(set(refined["content_pillars"][0]["example_content_ideas"])) == 3


def test_refine_step5_output_cleans_front_door_offer_names():
    result = {
        "DOSER": {
            "own": {"freebie_idea": "Autonomous Agency Prospecting System: Templates and Blueprints to Generate 50 Leads/Week with AI"},
            "sell": {"product_idea": "Autonomous Agency Prospecting System: Templates and Blueprints to Generate 50 Leads/Week with AI"}
        },
        "Layered Offers": {
            "free_value_layer": {"free_resource": "AI Prospecting Workflow Kit"},
            "tier_3_high_ticket": {"product_name": "AI Business Rebuild coaching"}
        },
    }

    refined = main.refine_step5_output(result)

    assert refined["DOSER"]["sell"]["product_idea"] == "AI Prospecting Workflow Kit"
    assert refined["DOSER"]["own"]["freebie_idea"] != refined["DOSER"]["sell"]["product_idea"]
    assert refined["Layered Offers"]["tier_3_high_ticket"]["product_name"] == "AI Business Rebuild Coaching"


def test_refine_step2_output_derives_clean_tagline_from_brief():
    result = {
        "branded_message": {
            "core_message": "bad",
            "tagline": "bad",
        },
        "blueprint": {"niche_you_become": "bad"},
    }

    refined = main.refine_step2_output(
        result,
        "FRONT-DOOR POSITIONING:\n- Audience: solo operators\n- Core promise: I show solo entrepreneurs how to automate their business so they work less and live more.\n- Real pain to lead with: doing everything themselves.\n- Outcomes to emphasize: get clients without hiring, buy back time.\n- Creator credibility: rebuilt solo after a partnership blowup.\n- Tagline flavor only: old tagline\n",
        model_choice="GPT-5.3",
    )

    assert refined["branded_message"]["tagline"] == "Work Less. Live More."
    assert refined["blueprint"]["niche_you_become"] == "The solo operator who rebuilt with automation."


def test_refine_step2_output_simplifies_blueprint_pillars():
    result = {
        "branded_message": {},
        "blueprint": {
            "content_pillars": [
                {
                    "pillar": "AI Builds",
                    "description": "Hands-on breakdowns of wiring AI into agency workflows.",
                    "example_post": "Tired of VA churn killing your agency margins? Watch me build an AI SDR that prospects 100 leads.",
                },
                {
                    "pillar": "Nomad Grind",
                    "description": "Patong rebuild stories tying Muay Thai discipline to AI output.",
                    "example_post": "Woke up in Thailand, hit pads, then let my AI agents close deals by noon.",
                },
            ]
        },
    }

    refined = main.refine_step2_output(
        result,
        "FRONT-DOOR POSITIONING:\n- Audience: solo operators\n- Core promise: I show solo entrepreneurs how to automate their business so they work less and live more.\n- Real pain to lead with: doing everything themselves.\n- Outcomes to emphasize: get clients without hiring, buy back time.\n- Creator credibility: rebuilt solo after a partnership blowup.\n",
        model_choice="GPT-5.3",
    )

    assert refined["blueprint"]["content_pillars"][0]["description"] == "Show the systems that save time, win clients, or remove repetitive work."
    assert refined["blueprint"]["content_pillars"][1]["description"] == "Show how you keep work under control while living abroad."


def test_refine_step1_output_simplifies_pillar_copy_and_truth_angles():
    result = {
        "content_pillars": [
            {
                "name": "AI BUILDS",
                "description": "Hands-on breakdowns of anti-detect setups, multi-agent systems, and cloud GPU workflows.",
                "example_content_ideas": ["How I built an AI agent that prospects clients using only public data"],
            }
        ],
        "your_truth": {
            "most_powerful_content_angles": [
                {
                    "angle": "2AM Debugs",
                    "story_hook": "Nights fixing SageAttention on H100s because pipelines had to ship.",
                }
            ]
        },
        "weekly_balance": {
            "rationale": "Heavy anchor output drives algorithmic visibility and partnerships with AI tools."
        },
    }

    refined = main.refine_step1_output(result, "brief", model_choice="GPT-5.3")

    assert refined["content_pillars"][0]["description"] == "Show the systems that save time, bring in clients, or remove repetitive work."
    assert refined["your_truth"]["most_powerful_content_angles"][0]["angle"] == "Late-Night Fixes"
    assert refined["your_truth"]["most_powerful_content_angles"][0]["story_hook"] == "What fixing broken systems late at night taught me about keeping things simple."
    assert refined["weekly_balance"]["rationale"] == "Let the practical build content carry the schedule, then use the personal stories to make people care."


def test_refine_step3_output_rewrites_resume_style_titles_and_scripts():
    result = [
        {
            "generic_version": "how I get clients without hiring a sales team",
            "positioned_version": "3 ways I get clients on $1K/month runway",
            "why_this_wins": "This ties the idea to Patong and my nomad rebuild story.",
            "opening_script": "Living lean in Patong means no room for sales hires. I built AI that hunts clients for me.",
        },
        {
            "generic_version": "how I make content without editing all day",
            "positioned_version": "My content system when I hate overwork",
            "why_this_wins": "This leans on my Muay Thai nomad life.",
            "opening_script": "Muay Thai keeps me sane in Patong, but AI handles it all while I train.",
        },
    ]

    refined = main.refine_step3_output(result, "brief", model_choice="GPT-5.3")

    assert refined[0]["positioned_version"] == "how I get clients without adding more hours"
    assert refined[0]["opening_script"] == "If I had to find clients again without working more hours, this is the first system I'd build. It takes a job I used to do by hand and turns it into something repeatable."
    assert refined[1]["positioned_version"] == "the content setup I use when I do not want to burn out"
    assert refined[1]["opening_script"] == "I got tired of spending half the day editing instead of publishing. This is the setup I use to keep posting without letting content take over the whole week."


def test_refine_hook_lines_rewrites_duplicates_and_creator_slop():
    hooks = [
        "Capped at $5K months for endless hours? How I'd automate client hunting to buy back your time.",
        "Capped at $5K months for endless hours? How I'd automate client hunting to buy back your time.",
        "If client work is killing your nomad dreams, here's how I'd automate the grind so you live the nomad life.",
    ]

    refined = main.refine_hook_lines(hooks, kind="hook", positioning_brief="brief", model_choice="GPT-5.3")

    assert refined == [
        "If you're doing everything yourself, this is the first thing I'd automate.",
        "If your income only moves when you work more, this is the workflow I'd fix first.",
        "If client work eats your whole week, this is how I'd buy back time first.",
    ]


def test_refine_step5_output_simplifies_offer_copy_and_promises():
    result = {
        "Layered Offers": {
            "free_value_layer": {
                "content_ideas": [
                    "Trading 12-hour days for $10K/month? Watch me automate client prospecting in 60 seconds.",
                    "Muay Thai at 6AM, then AI agents close deals while I train—here's the setup.",
                ],
            },
            "tier_2_mid_ticket": {
                "product_name": "Autonomous Agency Workflow Course",
            },
            "tier_3_high_ticket": {
                "product_name": "AI Business Rebuild coaching",
                "results_promise": "Cut client acquisition time by 80%, generate 50+ warm leads/month autonomously, reclaim 20+ hours/week.",
            },
        }
    }

    refined = main.refine_step5_output(result)

    assert refined["Layered Offers"]["tier_2_mid_ticket"]["product_name"] == "Solo Operator Automation Course"
    assert refined["Layered Offers"]["tier_3_high_ticket"]["product_name"] == "AI Business Rebuild Coaching"
    assert refined["Layered Offers"]["tier_3_high_ticket"]["results_promise"] == "Help you remove manual work, tighten your offer, and build simpler systems you can actually use."
    assert refined["Layered Offers"]["free_value_layer"]["content_ideas"][0] == "Doing everything yourself? This is the first part of the work I'd automate."


def test_refine_step6_output_rewrites_salesy_convert_hooks():
    hooks = [
        "If client work is killing your nomad dreams, the AI Prospecting Workflow Kit at $97 is what got me shipping from Thailand without burnout.",
        "If everything takes forever without a team, this AI Prospecting Workflow Kit gave me systems to hit $10K months solo.",
    ]

    refined = main.refine_step6_output(hooks, "brief", model_choice="GPT-5.3")

    assert refined == [
        "If finding clients still eats too much of your week, start with the AI Prospecting Workflow Kit.",
        "If everything in your business still needs you, the AI Prospecting Workflow Kit is the first place I would start.",
    ]


def test_pipeline_step4_returns_clean_502_for_invalid_ai_response(monkeypatch):
    monkeypatch.setattr(
        main,
        "call_ai",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            main.InvalidAIResponseError(
                "Malformed AI response from Claude Sonnet during step4_hooks.",
                raw_response='{"hooks":["good"], "broken"}',
            )
        ),
    )

    req = main.Step4Request(
        story="story",
        skills="skills",
        audience="audience",
        situation="situation",
        step1_result={
            "core_message": "message",
            "content_pillars": [{"name": "AI BUILDS", "description": "desc", "is_anchor": True}],
            "avatar": {},
        },
        step2_result={
            "branded_message": {"tagline": "tagline"},
            "blueprint": {"niche_you_become": "niche"},
        },
    )

    with pytest.raises(HTTPException) as exc:
        main.pipeline_step4(req)

    assert exc.value.status_code == 502
    assert exc.value.detail == (
        "AI returned malformed structured output during step4_hooks. "
        "The raw response was logged on the server."
    )
