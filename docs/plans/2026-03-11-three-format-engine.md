# Three-Format Unified Script Engine

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend stratalyzer's `rewrite` command to produce three output formats (caption, short, full) from a single engine, powered by the strategy document's extracted principles.

**Architecture:** One system prompt (theory-first, already proven). One user prompt per format with format-specific structural constraints. The `--format` flag on the existing `rewrite` CLI command selects which constraints apply. No new files, no new modules — modifications to `scriptgen.py` and `cli.py` only.

**Tech Stack:** Python, Click, Anthropic Claude API (claude-sonnet-4-6), existing stratalyzer codebase

---

## Principle Analysis

### Which extracted principles apply to script generation?

Of 44 total principles (15 topics, 15 processes, 14 frameworks), **20 are script-craft principles** that directly affect how a script is written, and **24 are meta-strategy principles** about content planning, branding, and personal development.

#### Script-Craft Principles (power the engine)

| # | Source | Principle | Caption (10-20 words) | Short (25-45 words, 7-15s) | Full (150-200 words, 50-60s) |
|---|--------|-----------|:---------------------:|:--------------------------:|:----------------------------:|
| 1 | Hook Writing | Super Hook (credibility 2nd line) | NO | YES (compressed) | YES (full) |
| 2 | Hook Writing | Speed-to-value / no slow intros | YES | YES | YES |
| 3 | Hook Writing | Curiosity hooks, open/close loops | NO (too short) | YES (one loop) | YES (nested loops) |
| 4 | Hook Writing | Connector words ("but", "so") for tension | NO | YES | YES |
| 5 | Hook Writing | Contrarian hooks | YES | YES | YES |
| 6 | Hook Writing | Non-obvious take / dopamine hit | YES (core driver) | YES (core driver) | YES (core driver) |
| 7 | Hook Writing | Re-hooks mid-video | NO | NO | YES |
| 8 | Hook Writing | Hypothetical twist -> strategic pause -> payoff | NO | NO | YES |
| 9 | Viral Mechanics | Reframe common truth in surprising way | YES | YES | YES |
| 10 | Viral Mechanics | Present problem before solution | NO (too short) | YES | YES |
| 11 | Viral Mechanics | Make audience feel seen (name the emotion) | YES | YES | YES |
| 12 | Viral Mechanics | Captions for sound-off viewers | N/A (IS the caption) | NO (spoken) | NO (spoken) |
| 13 | Viral Mechanics | Package familiar ideas counterintuitively | YES | YES | YES |
| 14 | TAM | Broad hook -> niche value | NO | YES (compressed) | YES |
| 15 | Framework: Non-Obvious Take | Familiar + surprising = dopamine | YES | YES | YES |
| 16 | Framework: Open/Closed Loop | Open loops, re-hooks, twist mechanism | NO | YES (one loop) | YES (multiple) |
| 17 | Framework: Credibility-First | Lead with why they should trust you | NO | YES (super hook) | YES (super hook) |
| 18 | Framework: TAM Targeting | Balanced TAM + non-obvious angle + biz connection | NO | Partial | YES |
| 19 | Process: Super Hook Creation | Hook -> credibility line (results or effort) | NO | YES | YES |
| 20 | Framework: Counter Positioning | Break the dominant pattern in your niche | YES (angle) | YES (angle) | YES (angle) |

#### Meta-Strategy Principles (context/knowledge, NOT writing instructions)

These stay in the strategy document as reference knowledge (the existing `topics_text` section in the system prompt). They inform the LLM about the influencer's worldview and can be cited as evidence, but they do NOT become structural rules:

- Trial Reels system, Three-List system, MEC system, Content Growth Milestones (content planning)
- Content Monetization Funnel, Sell Before Build, Offer Creation (business strategy)
- 80/20 Balance, Warren Buffett framework (posting strategy)
- Competitor Audit, Asian Creator Positioning, Inferior Advantage (personal branding)
- 100 Reps Sprint, Action-Before-Readiness, Acceptance/Resilience, Social Circle Audit (mindset)
- AI Content Differentiation, Custom GPT Setup (tools/trends)
- Power & Status Signaling (one-off anecdote)
- Tactical vs Principle Expert (positioning advice)

---

## Format Specifications

### Format 1: Caption (`--format caption`)
- **What it is**: Text pasted over b-roll. No voice. Reader sees it for 3-5 seconds.
- **Length**: 10-20 words per caption. 1-3 captions per transcript.
- **Structure**: ONE non-obvious take. No hook/body/payoff — the entire thing IS the take.
- **Active principles**: Non-obvious reframe, contrarian angle, speed-to-value, make audience feel seen
- **Inactive principles**: Super hooks, open loops, re-hooks, mid-video twists, problem-before-solution (no room)
- **Voice**: Punchy. Declarative. No hedging. Statement, not story.
- **Example**: "The couples who post the least are usually the happiest."
- **Output JSON**: `[{text, timestamp_start, timestamp_end, original_quote}]`

### Format 2: Short Talking Head (`--format short`)
- **What it is**: Spoken to camera. One coherent argument compressed tight.
- **Length**: 25-45 words, 7-15 seconds at ~170 WPM.
- **Structure**: Hook (open loop, 1 sentence) -> Evidence/tension (1-2 sentences) -> Payoff (reframe, 1 sentence). No super hook unless it fits in <=8 words.
- **Active principles**: Open loop hook, non-obvious take, contrarian angle, connector words, speed-to-value, problem-before-solution (compressed)
- **Partially active**: Super hook (only if <=8 words), TAM balancing
- **Inactive**: Re-hooks, mid-video twists, nested loops, hypothetical twists (no room)
- **Voice**: Conversational, spoken rhythm. Fragments OK. Contractions required.
- **Output JSON**: `[{script, caption (3-7 words, different info, works on mute), timestamp_start, timestamp_end, original_quote}]`

### Format 3: Full Talking Head (`--format full`, default)
- **What it is**: Current strat output. Full script with stage directions.
- **Length**: 150-200 spoken words, 50-60 seconds.
- **Structure**: Hook -> Super Hook -> Body (building argument with open loops, re-hooks) -> Payoff -> CTA
- **All principles active**, including nested loops, re-hooks, hypothetical twists, mid-video tension beats, broad TAM -> niche value
- **Voice**: Natural speech with strategic rhythm. Longer sentences OK when building momentum.
- **Output**: Existing `rewrite_script()` output format (prose with stage directions)

---

## Implementation Plan

### Task 1: Add FORMAT SCALING theory to system prompt

**Files:**
- Modify: `src/stratalyzer/scriptgen.py:19-103` (`_build_system_prompt()`)

**Step 1: Add format scaling section to the end of the system prompt**

Append this after the `## OUTPUT FORMAT` section (before the closing triple-quote) in `_build_system_prompt()`:

```python
# Add after the OUTPUT FORMAT section, before the closing triple-quote:

## FORMAT SCALING

The same principles apply at every length. What changes is STRUCTURE:

**CAPTION (text overlay, 10-20 words):** The entire piece IS the non-obvious take. No hook/body/payoff \
structure — one reframe, stated as fact. The punch IS the piece. Must pass the "screenshot test" — if \
someone screenshots just the text and shares it, does it still hit?

**SHORT (7-15 seconds, 25-45 words):** Hook opens ONE loop (unanswered question). 1-2 sentences of \
evidence or tension. Payoff closes the loop as a reframe. No super hook unless it fits in 8 words or \
fewer. No CTA. No stage directions. Every word earns its place.

**FULL (50-60 seconds, 150-200 words):** Hook -> Super Hook -> Body (single building argument with \
open loops and re-hooks) -> Payoff -> CTA. Full structure with stage directions. Every line advances \
the ONE central argument.

At any length: no slow intros, no hedging, no cliches, no invented details. The non-obvious take / \
dopamine hit is the universal principle — it works at 10 words and at 200 words.
```

**Step 2: Run existing tests to verify nothing breaks**

```bash
cd C:/Users/asus/Desktop/projects/stratalyzer
pytest tests/ -v
```
Expected: All existing tests PASS

**Step 3: Commit**

```bash
git add src/stratalyzer/scriptgen.py
git commit -m "feat: add format scaling theory to system prompt"
```

---

### Task 2: Add format parameter and format-specific user prompts to `rewrite_script()`

**Files:**
- Modify: `src/stratalyzer/scriptgen.py:139-169` (`rewrite_script()`)

**Step 1: Add format parameter and format-specific prompt logic**

Change `rewrite_script()` signature to accept `format` parameter and use format-specific user prompts:

```python
def rewrite_script(
    strategy_path: Path,
    transcript: str,
    funnel_position: str = "middle",
    duration: int = 60,
    format: str = "full",
) -> str:
    """Rewrite a rambling transcript into a script.

    Args:
        format: "caption" (10-20 word text overlays), "short" (25-45 word talking head),
                or "full" (150-200 word full script, default)
    """
    strategy = _load_strategy(strategy_path)
    system_prompt = _build_system_prompt(strategy)

    if format == "caption":
        user_prompt = f"""Distill this transcript into 1-3 on-screen text overlays (10-20 words each).

Each is a STANDALONE non-obvious take — a familiar truth reframed in a way the reader has never seen \
it stated. It will be pasted as text over b-roll video. No voice. Reader sees it for 3-5 seconds.

Rules:
- Use the speaker's actual points. Do not invent.
- Declarative statement, not a story. No "I" unless the speaker's identity IS the point.
- Must pass the "screenshot test" — if someone screenshots just the text and shares it, does it still hit?
- Deduplicate. If the speaker made one point, output one caption.

**Raw transcript:**
{transcript}

Return a JSON array. Each object:
- "text": the on-screen text (10-20 words)
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
        user_prompt = f"""Below is a raw, unedited transcript from a video. The speaker had good ideas \
but the delivery is rambling and unstructured.

Your job: extract the core ideas and arguments from this transcript, then rewrite it as a tight, \
coherent short-form video script. Keep the speaker's ACTUAL points and insights — do not invent new \
information. Restructure and sharpen what's already there.

**Raw transcript:**
{transcript}

**Funnel position:** {funnel_position}
**Target duration:** ~{duration} seconds

Before writing, identify: what is the ONE core argument buried in this ramble? Build the entire script \
around that single argument. Use the speaker's own points as evidence, but arrange them so every line \
builds on the last. Cut anything that doesn't serve the argument — even if the speaker said it."""

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()
```

**Step 2: Verify existing tests still pass**

```bash
pytest tests/ -v
```

**Step 3: Commit**

```bash
git add src/stratalyzer/scriptgen.py
git commit -m "feat: add caption and short format support to rewrite_script"
```

---

### Task 3: Add `--format` flag to CLI `rewrite` command

**Files:**
- Modify: `src/stratalyzer/cli.py:164-195` (`rewrite` command)

**Step 1: Add the `--format` option**

Add `@click.option("--format", "-F", ...)` to the rewrite command and pass it through:

```python
@main.command()
@click.argument("strategy", type=click.Path(exists=True, dir_okay=False))
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option("--format", "-F", "output_format", default="full",
              type=click.Choice(["caption", "short", "full"]),
              help="Output format: caption (text overlay), short (7-15s script), full (50-60s script)")
@click.option("--funnel", "-f", default="middle", type=click.Choice(["top", "middle", "bottom"]), help="Funnel position")
@click.option("--duration", "-d", default=60, help="Target duration in seconds")
def rewrite(strategy: str, source: str, output_format: str, funnel: str, duration: int):
    """Rewrite a rambling video/transcript into a tight script.

    SOURCE can be a video file (.mp4, .mov, .webm) or a text file (.txt) containing a transcript.
    """
    source_path = Path(source)
    video_exts = {".mp4", ".mov", ".webm"}

    if source_path.suffix.lower() in video_exts:
        console.print(f"[bold]Transcribing {source_path.name}...[/bold]")
        from stratalyzer.transcriber import transcribe_video
        transcript = transcribe_video(source_path)
        if not transcript:
            console.print("[red]Could not extract transcript from video.[/red]")
            return
        console.print(f"[green]Transcript: {len(transcript.split())} words[/green]")
    else:
        transcript = source_path.read_text(encoding="utf-8").strip()
        if not transcript:
            console.print("[red]Source file is empty.[/red]")
            return
        console.print(f"[green]Loaded transcript: {len(transcript.split())} words[/green]")

    format_labels = {"caption": "text overlay captions", "short": "short talking head script", "full": "full script"}
    console.print(f"[bold]Generating {format_labels[output_format]}...[/bold]")
    result = rewrite_script(Path(strategy), transcript, funnel, duration, format=output_format)
    click.echo()
    click.echo(result)
```

**Step 2: Test all three formats manually**

```bash
# Create a small test transcript
echo "So basically what I realized is that most people never ship because they keep trying to find the perfect idea from the outside. But the thing is you need to solve a problem for yourself first. If you were the only person on earth who would use it you would still use it. That is how you know you have a real idea." > test_transcript.txt

# Test each format
stratalyzer rewrite iamchrischung/strategy.json test_transcript.txt --format caption
stratalyzer rewrite iamchrischung/strategy.json test_transcript.txt --format short
stratalyzer rewrite iamchrischung/strategy.json test_transcript.txt --format full

# Cleanup
rm test_transcript.txt
```

Expected:
- `caption`: JSON array with 1-3 items, each with `text` field of 10-20 words
- `short`: JSON array with 1-3 items, each with `script` field of 25-45 words + `caption` field
- `full`: Prose script with HOOK/SUPER HOOK/SCRIPT/CTA structure

**Step 3: Commit**

```bash
git add src/stratalyzer/cli.py
git commit -m "feat: add --format flag to rewrite command (caption/short/full)"
```

---

## What This Replaces

After this implementation, **Ramble Distiller's functionality is fully covered by stratalyzer**:

| Ramble Distiller Function | Stratalyzer Equivalent |
|---------------------------|----------------------|
| `distill()` with `format="text_overlay"` | `stratalyzer rewrite --format caption` |
| `distill()` with `format="talking_head"` | `stratalyzer rewrite --format short` |
| N/A (ramble couldn't do this) | `stratalyzer rewrite --format full` |

Stratalyzer's advantage: it has the **strategy document as context** (all 44 extracted principles from the influencer's actual content), plus the **theory-first system prompt** that produces coherent output instead of mechanical checklist output.

---

## Usage After Implementation

```bash
# Analyze influencer content (existing)
stratalyzer analyze influencer_folder/

# Generate scripts from topic (existing)
stratalyzer script strategy.json "weight loss" --funnel top

# Rewrite rambling video into text overlay captions (NEW)
stratalyzer rewrite strategy.json rambling_video.mp4 --format caption

# Rewrite rambling video into short talking head script (NEW)
stratalyzer rewrite strategy.json rambling_video.mp4 --format short

# Rewrite rambling video into full script (existing, now default)
stratalyzer rewrite strategy.json rambling_video.mp4 --format full

# Also works with text transcripts
stratalyzer rewrite strategy.json transcript.txt --format short
```
