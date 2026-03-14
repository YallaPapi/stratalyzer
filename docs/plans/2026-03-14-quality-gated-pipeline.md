# Quality-Gated Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an internal quality gate so the pipeline rewrites weak, cliché, or technical slop before it reaches the user.

**Architecture:** Keep the six-step API contract intact, but insert a deterministic issue detector plus an editor/rewrite pass for Step 3, Step 4, and Step 6 text outputs. Tighten product-name cleanup so monetization outputs also stay in plain-English buyer language.

**Tech Stack:** FastAPI, Pydantic, pytest, Next.js.

---

### Task 1: Add tests for slop detection

**Files:**
- Modify: `tests/test_pipeline_api.py`
- Modify: `api/main.py`

**Step 1: Write the failing tests**

Add tests that prove:
- cliché phrases are flagged (`while you sleep`, `bulletproof`, beach-freedom language)
- generic creator slop is flagged (`client-prospecting agent`, `public-data reports`, `no team`, `40s nomad`)
- plain spoken hooks are not flagged

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement a `find_quality_issues` helper in `api/main.py`.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: PASS

### Task 2: Add rewrite gate for Step 3, Step 4, and Step 6

**Files:**
- Modify: `api/main.py`
- Modify: `tests/test_pipeline_api.py`

**Step 1: Write the failing tests**

Add tests showing:
- low-quality Step 3 titles trigger rewrite gating
- low-quality hooks trigger rewrite gating
- clean hooks bypass the gate

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: FAIL

**Step 3: Write minimal implementation**

Add:
- quality issue detector
- editor prompt + rewrite helper
- loop with max retries for Step 3/4/6 outputs

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: PASS

### Task 3: Tighten product-name cleanup

**Files:**
- Modify: `api/main.py`
- Modify: `tests/test_pipeline_api.py`

**Step 1: Write the failing test**

Add tests for names like `Empire Builder`, `Accelerator`, `Blueprint`, and mixed-case weirdness.

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: FAIL

**Step 3: Write minimal implementation**

Normalize product names into buyer-readable names while preserving meaning.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pipeline_api.py -q`
Expected: PASS

### Task 4: Live replay and verification

**Files:**
- Modify: `api/main.py` if further fixes are needed

**Step 1: Replay the saved creator input**

Run the saved input from `api/logs/pipeline_api_20260314_112619.json`.

**Step 2: Evaluate the output**

Reject and iterate if:
- Step 3 still sounds like tech résumé content
- Step 4 still contains cliché creator-marketing copy
- Step 6 still sounds like ad copy instead of creator language

**Step 3: Run final verification**

Run:
- `pytest -q`
- `npm.cmd run build`

Expected: both PASS
