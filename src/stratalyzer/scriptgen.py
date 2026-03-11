import json
from pathlib import Path
from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def _load_strategy(strategy_path: Path) -> dict:
    return json.loads(strategy_path.read_text(encoding="utf-8"))


def _build_system_prompt(strategy: dict) -> str:
    """Build system prompt from the strategy document."""
    processes_text = ""
    for proc in strategy.get("processes", []):
        processes_text += f"\n- **{proc['name']}**: {proc['description']}"

    frameworks_text = ""
    for fw in strategy.get("frameworks", []):
        frameworks_text += f"\n- **{fw['name']}**: {fw['description']}"

    topics_text = ""
    for topic, points in strategy.get("topics", {}).items():
        topics_text += f"\n### {topic}\n"
        for point in points:
            topics_text += f"- {point}\n"

    return f"""You are a world-class short-form video scriptwriter. You write scripts for Instagram Reels, TikTok, and YouTube Shorts.

## THEORY: HOW A GREAT SHORT-FORM VIDEO WORKS

A great short-form video is ONE coherent argument from start to finish. Every single line must advance that ONE argument. There are no tangents, no topic switches, no filler.

Here is the viewer's psychological journey through a perfect video:

**1. THE HOOK (first 1-3 seconds)** — The viewer is scrolling. You have one line to make them stop. The hook creates a SPECIFIC knowledge gap, tension, or contradiction in the viewer's mind. It makes them think "wait, what?" or "that can't be right" or "I need to know more." The hook is the THESIS of the entire video — everything that follows must deliver on this exact promise.

**2. THE SUPER HOOK (next 2-3 seconds)** — The viewer stopped scrolling but hasn't committed. The super hook answers "why should I listen to YOU about this?" It's a credibility line — either a specific result you achieved or effort you invested. It must be directly relevant to the hook's claim. If the hook is about weight loss, the super hook is about YOUR weight loss experience, not something unrelated.

**3. THE BODY** — This is where you DELIVER on the hook's promise. The body is a single, building argument — not a list of loosely related tips. Each sentence must logically follow from the previous one. The viewer should feel the argument tightening, getting more specific, more compelling. Think of it as a chain: if you remove any link, the argument breaks.

The body uses these techniques to keep viewers engaged:
- **Open loops**: Tease something coming ("and here's where it gets interesting...") to create forward momentum. But the tease must be ABOUT THE SAME ARGUMENT, not a new topic.
- **Non-obvious angle**: Present the familiar topic from a perspective the viewer has never considered. This is what creates the dopamine hit — a relatable truth reframed in a surprising way.
- **Problem before solution**: Make the viewer FEEL the problem viscerally before offering the fix. They need to feel the pain to value the cure.
- **Mid-video re-hook**: When you sense the viewer might drop off, open a new curiosity gap — but it must be a DEEPER layer of the same argument, not a new subject.

**4. THE PAYOFF** — Close every loop you opened. Deliver the insight the hook promised. The viewer should feel "oh, THAT'S why they said that at the start." The payoff ties back to the opening — the entire video is one circle.

**5. THE CTA** — A natural, organic call to action. It should feel like the logical next step after the argument you just made, not a bolted-on sales pitch.

## THE CRITICAL RULE

The hook, super hook, body, and payoff are ALL PART OF ONE THOUGHT. If you read just the hook and then skip to the payoff, it should still make sense as the same argument. The body is not a detour — it's the bridge between the promise and the delivery.

If at any point a line does not directly build on the previous line or advance the hook's central argument, DELETE IT. Coherence over cleverness. Every line earns its place by advancing the ONE idea.

## STYLE

- Written for spoken delivery. Natural speech patterns, not essay prose.
- No slow intros. First dopamine hit within 3-5 seconds.
- Trim all dead space. Every sentence carries information or emotion.
- 80% educational value, 20% personality and voice.
- Specific numbers, examples, and details over vague claims.
- Stage directions in brackets: [cut to B-roll], [text on screen: "key stat"], [pause for emphasis].

## TOOLKIT — PROVEN TECHNIQUES

These are techniques extracted from high-performing content. Use them as tools to strengthen your argument — do NOT treat them as a checklist to mechanically execute.
{processes_text}
{frameworks_text}

## TOPIC EXPERTISE

Use these as reference knowledge when the topic is relevant:
{topics_text}

## OUTPUT FORMAT

```
HOOK: [the opening line]

SUPER HOOK: [credibility line — must be relevant to the hook]

SCRIPT:
[The full script as one continuous, coherent argument. Include stage directions in brackets. Write it exactly as it would be spoken aloud.]

CTA: [organic call to action]

---
NOTES:
- Core argument (one sentence): [what is the ONE thesis of this video?]
- Hook type: [curiosity/contrarian/pattern-interrupt]
- Techniques used: [which toolkit items you applied and where]
- Estimated length: [seconds]
```

## FORMAT SCALING

The same principles apply at every length. What changes is STRUCTURE:

**CAPTION (text overlay, 35-60 words):** One flowing non-obvious take pasted over b-roll. Deliberately \
too long to read in a single 7-second viewing — forces replays. Structure: setup -> tension -> reframe \
as one continuous thought. Must pass the "screenshot test" — if someone screenshots just the text and \
shares it, does it still hit?

**SHORT (7-15 seconds, 25-45 words):** Hook opens ONE loop (unanswered question). 1-2 sentences of \
evidence or tension. Payoff closes the loop as a reframe. No super hook unless it fits in 8 words or \
fewer. No CTA. No stage directions. Every word earns its place.

**FULL (50-60 seconds, 150-200 words):** Hook -> Super Hook -> Body (single building argument with \
open loops and re-hooks) -> Payoff -> CTA. Full structure with stage directions. Every line advances \
the ONE central argument.

At any length: no slow intros, no hedging, no cliches, no invented details. The non-obvious take / \
dopamine hit is the universal principle — it works at 10 words and at 200 words."""


def generate_script(
    strategy_path: Path,
    topic: str,
    funnel_position: str = "middle",
    duration: int = 60,
    num_scripts: int = 1,
) -> str:
    """Generate video script(s) based on the strategy document."""
    strategy = _load_strategy(strategy_path)
    system_prompt = _build_system_prompt(strategy)

    user_prompt = f"""Write {num_scripts} video script(s).

**Topic:** {topic}
**Funnel position:** {funnel_position}
**Target duration:** ~{duration} seconds

Before writing, decide: what is the ONE core argument this video makes? Write that down first. Then build every line of the script to advance that single argument from hook to payoff. If a line doesn't serve the argument, cut it."""

    if num_scripts > 1:
        user_prompt += f"\n\nSeparate each script with a line of ===."

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()


def rewrite_script(
    strategy_path: Path,
    transcript: str,
    funnel_position: str = "middle",
    duration: int = 60,
    format: str = "full",
) -> str:
    """Rewrite a rambling transcript into a script.

    Args:
        format: "caption" (35-60 word text overlay, forces replay), "short" (25-45 word talking head),
                or "full" (150-200 word full script, default)
    """
    strategy = _load_strategy(strategy_path)
    system_prompt = _build_system_prompt(strategy)

    if format == "caption":
        user_prompt = f"""Distill this transcript into 1 on-screen text overlay (35-60 words).

This text will be pasted over b-roll video (walking footage, scenery, etc). No voice. The text should \
be DELIBERATELY too long to read in a single 7-second watch — the viewer must replay the video to \
finish reading it. This forces multiple views, which is the entire point.

The text is ONE non-obvious take — a familiar truth reframed in a way the reader has never seen it \
stated. It should read like a punchy, compressed argument: setup -> tension -> reframe. Not a list, \
not bullet points — one flowing thought that builds and lands.

Rules:
- Use the speaker's actual points. Do not invent.
- Must pass the "screenshot test" — if someone screenshots just the text and shares it, does it still hit?
- Deduplicate. If the speaker made one point, output one caption.
- The text must be too long to comfortably read in one viewing. This is intentional.

**Raw transcript:**
{transcript}

Return a JSON array. Each object:
- "text": the on-screen text (35-60 words, too long to read in one viewing)
- "timestamp_start": approximate start time in transcript
- "timestamp_end": approximate end time in transcript
- "original_quote": the original text this was distilled from

Return ONLY valid JSON array, no other text."""

    elif format == "short":
        user_prompt = f"""Distill this transcript into 1-3 talking head scripts (25-45 words each, \
7-15 seconds spoken at ~170 WPM).

Each is ONE coherent argument: hook (open loop) -> evidence -> payoff (reframe).
No super hook unless it fits in 8 words or fewer. No CTA. No stage directions.

Rules:
- Use the speaker's actual words and points. Do not invent.
- Hook must create an unanswered question. Payoff must answer it as a reframe.
- Written for speaking: contractions, fragments, rhythm.
- Deduplicate ruthlessly. Same point = one script, not three.

**Raw transcript:**
{transcript}

Return a JSON array. Each object:
- "script": full spoken script (25-45 words)
- "caption": on-screen text (3-7 words, DIFFERENT info than script, works on mute)
- "timestamp_start": approximate start time in transcript
- "timestamp_end": approximate end time in transcript
- "original_quote": the original text this was distilled from

Return ONLY valid JSON array, no other text."""

    else:  # full
        user_prompt = f"""Below is a raw, unedited transcript from a video. The speaker had good ideas but the delivery is rambling and unstructured.

Your job: extract the core ideas and arguments from this transcript, then rewrite it as a tight, coherent short-form video script. Keep the speaker's ACTUAL points and insights — do not invent new information. Restructure and sharpen what's already there.

**Raw transcript:**
{transcript}

**Funnel position:** {funnel_position}
**Target duration:** ~{duration} seconds

Before writing, identify: what is the ONE core argument buried in this ramble? Build the entire script around that single argument. Use the speaker's own points as evidence, but arrange them so every line builds on the last. Cut anything that doesn't serve the argument — even if the speaker said it."""

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()


def generate_hooks(
    strategy_path: Path,
    topic: str,
    count: int = 10,
) -> str:
    """Generate hook variations for a topic."""
    strategy = _load_strategy(strategy_path)
    system_prompt = _build_system_prompt(strategy)

    user_prompt = f"""Generate {count} hook + super hook combinations for this topic:

**Topic:** {topic}

For each, provide:
1. The HOOK (first line — what stops the scroll)
2. The SUPER HOOK (credibility/authority line)
3. Hook type (curiosity / contrarian / pattern-interrupt / non-obvious)

Format each as:
```
[#] HOOK: ...
    SUPER HOOK: ...
    Type: ...
```

Make each one distinctly different. Range from safe to wild. At least 3 should be contrarian or polarizing."""

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()


def generate_ideas(
    strategy_path: Path,
    count: int = 20,
    pillar: str | None = None,
) -> str:
    """Generate content ideas using the Three-List system."""
    strategy = _load_strategy(strategy_path)

    topics_list = list(strategy.get("topics", {}).keys())

    user_prompt = f"""Using the Three-List Content Generation System, generate {count} content ideas.

The three lists to mix from:

**List 1 — Post Formats:**
- Talking head to camera
- Green screen with reference content
- Split screen reaction/breakdown
- B-roll with voiceover
- Text-on-screen carousel
- Screen recording walkthrough
- Podcast clip style

**List 2 — Content Pillars:**
{chr(10).join(f'- {t}' for t in topics_list)}

**List 3 — High-Demand Topics:**
(derive from the pillar and what the audience searches for)

{"Focus on pillar: " + pillar if pillar else "Mix across all pillars."}

For each idea, output:
```
[#] FORMAT + PILLAR + TOPIC
    Working title: "..."
    Non-obvious angle: ...
    Funnel position: top/middle/bottom
```

Apply the 80/20 rule: ~80% educational, ~20% personality/lifestyle."""

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=f"You are a content strategist for @{strategy.get('influencer', 'unknown')}. Generate creative, specific content ideas.",
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()
