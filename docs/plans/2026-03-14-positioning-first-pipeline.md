# Positioning-First Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework the active Next.js + FastAPI pipeline so outputs prioritize audience pain, simple outcomes, and creator credibility over technical mechanism.

**Architecture:** Keep the existing six-step flow and API contracts, but change the prompt logic and downstream data shaping so Step 1 extracts audience-facing positioning first, Step 2 turns creator details into credibility assets, and Steps 3-6 generate content ideas in plain-English market language. Preserve technical detail as proof/supporting material, not headline language.

**Tech Stack:** FastAPI, Pydantic, Python tests with pytest, Next.js/React TypeScript frontend.

---

### Task 1: Add regression tests for positioning-first outputs

**Files:**
- Modify: `tests/test_pipeline_api.py`
- Modify: `api/main.py`

**Step 1: Write the failing test**

Add tests that prove:
- Step 3 array parsing still works.
- A new helper can flag overly technical audience-facing phrases like `Vast.ai`, `SageAttention`, `anti-detect`, and `browser-auth`.
- The helper allows plain-English transformation language like `get more clients without hiring`.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: FAIL because the filtering/helper does not exist yet.

**Step 3: Write minimal implementation**

Add a small phrase filter / plain-English guard in `api/main.py` that can be used in Step 3-6 post-processing.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: PASS

### Task 2: Rewrite prompt intent for Step 1 and Step 2

**Files:**
- Modify: `api/main.py`

**Step 1: Write the failing test**

Add a focused test for a helper that converts creator context into a concise `positioning_brief` with:
- target audience
- painful problem
- desired outcome
- creator credibility
- mechanism translated into plain English

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: FAIL because the helper does not exist yet.

**Step 3: Write minimal implementation**

Implement the helper and thread its output into the Step 2 / Step 3 / Step 4 prompts. Update the prompts so:
- technical stack is demoted to proof
- audience value is promoted to headline language
- Thailand / AI / nomad details are treated as flavor and credibility, not the niche

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: PASS

### Task 3: Post-process generated hooks and angles

**Files:**
- Modify: `api/main.py`

**Step 1: Write the failing test**

Add tests proving the hook/angle normalizer:
- rewrites or rejects technical phrasing in titles/hooks
- preserves readable, audience-facing hooks

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: FAIL

**Step 3: Write minimal implementation**

Add a normalization pass for Step 3, Step 4, and Step 6 outputs that:
- strips banned technical headline terms
- falls back to broader value language
- keeps raw technical details only inside explanation/script fields when present

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: PASS

### Task 4: Update frontend labels for the new positioning language

**Files:**
- Modify: `frontend/src/components/StepResult.tsx`

**Step 1: Write the failing test**

Use a production build as the verification gate for TypeScript compatibility after rendering changes.

**Step 2: Run build to verify baseline**

Run: `npm.cmd run build`
Expected: PASS before changes.

**Step 3: Write minimal implementation**

Adjust labels/sections so the UI emphasizes:
- audience problem
- promised outcome
- credibility
- plain-English hooks

**Step 4: Run build to verify it passes**

Run: `npm.cmd run build`
Expected: PASS

### Task 5: Verify against the last real creator input

**Files:**
- Modify: `api/main.py` (if additional fixes required)

**Step 1: Re-run the exact saved input**

Run the same replay script against `api/logs/pipeline_api_20260314_112619.json`.

**Step 2: Verify output quality**

Expected:
- all six steps succeed
- Step 3 titles are audience-facing
- Step 4 hooks avoid backend jargon
- outputs read like marketable creator content, not system architecture notes

**Step 3: Run full verification**

Run:
- `pytest -q`
- `npm.cmd run build`

Expected: both PASS
