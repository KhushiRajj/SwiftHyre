# SwiftHyre Phase 4: Coding Assessment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let candidates complete a recruiter-authored coding challenge and provide recruiters with an auditable result.

**Architecture:** Keep challenge and hidden test-case data in the backend. Run source code only through the OnlineCompiler.io API when its current no-cost access is suitable; retain a provider interface for a self-hosted Judge0 fallback.

**Tech Stack:** Flask, PostgreSQL, React, OnlineCompiler.io API or Judge0, pytest, Vitest.

**Spec:** [../specs/2026-10-28-swifthire-design.md](../specs/2026-10-28-swifthire-design.md)

## Global Constraints

- **Never execute untrusted candidate code directly in the Flask application.**
- **Provider failures must be visible and must not be interpreted as candidate failures.**
- **Require recruiter approval before every candidate advancement or rejection.**
- **Do not store provider credentials in source code or expose them to the browser.**
- **Use hosted services only within verified no-cost terms; deployment costs may remain.**

## Review Focus

- Source code, language, or payloads exceeding configured limits must be rejected before provider calls — test in Task 1.
- Compiler timeout/unavailability must remain a provider error, not a failed candidate score — test in Task 2.
- Hidden tests and expected output must never appear in candidate API responses — test in Task 1.
- A retry must not duplicate a completed submission or score — test idempotency in Task 2.
- Unsupported language/provider configurations must be shown as unavailable, not silently mapped — test in Task 2.

---

### Task 1: Challenge authoring and candidate coding UI

**Files:**
- Create: `backend\src\swifthire\coding\models.py`, `backend\src\swifthire\coding\routes.py`, `backend\src\swifthire\coding\service.py`, `backend\tests\coding\test_challenges.py`
- Create: `frontend\src\features\coding\ChallengeEditor.tsx`, `frontend\src\features\coding\CandidateCodingPage.tsx`, `frontend\src\features\coding\CodingPages.test.tsx`
- Modify: `backend\src\swifthire\workflow\models.py`

**Interfaces:**
- Consumes: stage tokens and progression from Phase 3.
- Produces: recruiter-authored challenge (`title`, `prompt`, allowed languages, private input/expected-output test cases); candidate submission endpoint returns only public prompt, allowed languages, and public sample cases.

- [ ] **Step 1: Write failing tests** — assert challenge ownership, required prompt and at least one private test, candidate response omits private test data, and invalid/oversized submissions are rejected.
- [ ] **Step 2: Run `uv run pytest tests/coding/test_challenges.py -q`** — expected: challenge and submission routes are absent.
- [ ] **Step 3: Implement challenge persistence, owner checks, and candidate editor** — the browser may submit code but never receives private test inputs/expected outputs.
- [ ] **Step 4: Run backend/frontend challenge tests** — expected: recruiter creates a challenge and the authorized candidate sees only public data.
- [ ] **Step 5: Commit** — `feat: add coding challenge workflow` with the required Co-authored-by trailer.

### Task 2: Sandboxed execution and scored result

**Files:**
- Create: `backend\src\swifthire\coding\runner.py`, `backend\src\swifthire\coding\onlinecompiler.py`, `backend\src\swifthire\coding\scoring.py`, `backend\tests\coding\test_execution.py`
- Modify: `backend\src\swifthire\coding\service.py`

**Interfaces:**
- Produces: `CodeRunner.run(source: str, language: str, stdin: str, timeout_seconds: int) -> ExecutionResult`; `ExecutionResult(status: Literal["completed","timeout","unavailable","invalid"], stdout: str, stderr: str, duration_ms: int | None)`; `CodingResult.score_percentage` is an integer from 0 to 100 and remains a recommendation input only.

- [ ] **Step 1: Verify integration feasibility** — document OnlineCompiler.io API access, supported languages, limits, and current no-cost quota. If unsuitable, test a Judge0-compatible adapter plan; do not introduce a paid dependency.
- [ ] **Step 2: Write failing fake-provider tests** — assert all private cases are run server-side, only aggregate score/candidate-safe output is returned, timeout/unavailable is not scored as zero, and repeated submission is idempotent.
- [ ] **Step 3: Run `uv run pytest tests/coding/test_execution.py -q`** — expected: runner and scoring contract tests fail.
- [ ] **Step 4: Implement provider adapter and result states** — keep provider key server-side; enforce language/source/timeout limits; persist provider errors and allow retry without a duplicate score.
- [ ] **Step 5: Run all coding tests** — expected: fake-provider suite passes; perform a smoke test only if a verified no-cost provider account is configured.
- [ ] **Step 6: Commit** — `feat: add sandboxed coding assessment` with the required Co-authored-by trailer.
