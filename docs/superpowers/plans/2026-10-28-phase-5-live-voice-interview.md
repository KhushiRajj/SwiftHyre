# SwiftHyre Phase 5: Live AI Voice Interview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let invited candidates complete a live, two-way AI voice interview and give recruiters job-related, human-reviewable results.

**Architecture:** Discover and verify a cloud voice/model provider with a usable free tier before implementation. Keep provider credentials server-side, expose only short-lived session credentials, and persist consent, transcript, rubric evidence, and provider status separately from recruiter decisions.

**Tech Stack:** React, Flask, PostgreSQL, hosted cloud speech/realtime and LLM APIs with verified free tiers, pytest, Vitest.

**Spec:** [../specs/2026-10-28-swifthire-design.md](../specs/2026-10-28-swifthire-design.md)

## Global Constraints

- **For AI and voice, use hosted cloud APIs with usable free tiers; do not require local model runtimes.**
- **Do not silently substitute a local model or a paid service if no suitable tier exists; surface the limitation and defer that integration pending an approved alternative.**
- **Voice evaluation should assess role-relevant answers against a disclosed rubric, not accent, emotion, personality, or other proxies.**
- **The product needs a text alternative or equivalent accommodation path for candidates who cannot use voice.**
- **Obtain appropriate candidate disclosures and consent for voice interviews and external processing.**
- **Require recruiter approval before every candidate advancement or rejection.**

## Review Focus

- Missing voice consent must prevent starting an interview — test in Task 2.
- Provider credentials must never be returned to the browser; session credentials must expire — test in Task 1.
- Interrupted calls/provider failures must not produce a completed score — test in Task 2.
- Evaluation must not include accent/emotion/personality fields — test rubric schema and prompt contract in Task 2.
- A candidate requiring the text alternative must be able to complete a comparable interview flow — test in Task 3.

---

### Task 1: Provider feasibility and session boundary

**Files:**
- Create: `backend\src\swifthire\voice\base.py`, `backend\src\swifthire\voice\provider.py`, `backend\src\swifthire\voice\service.py`, `backend\tests\voice\test_provider_contract.py`
- Create: `docs\superpowers\voice-provider-decision.md`

**Interfaces:**
- Consumes: invited voice-interview stage from Phase 3.
- Produces: `VoiceInterviewProvider.create_session(candidate_id: UUID, interview_id: UUID, rubric: InterviewRubric) -> ProviderSession`; provider session includes an opaque provider session id and short-lived browser credential, never a long-lived API key.

- [ ] **Step 1: Verify a hosted provider** — confirm current no-cost quota, live bidirectional audio support, India availability, latency, data processing terms, and short-lived client credential support; record source URLs and limits in the decision note.
- [ ] **Step 2: Stop if no provider qualifies** — report the constraint and leave live voice integration deferred; do not switch to a paid API or local model.
- [ ] **Step 3: Write failing contract tests** — assert provider credentials stay server-side, browser token is short-lived, and unavailable provider yields an explicit `provider_unavailable` status.
- [ ] **Step 4: Implement provider contract and isolated fake** — no real provider calls in unit tests.
- [ ] **Step 5: Run `uv run pytest tests/voice/test_provider_contract.py -q`** — expected: all contract tests pass.
- [ ] **Step 6: Commit** — `feat: define hosted voice interview provider` with the required Co-authored-by trailer.

### Task 2: Consented live interview and scoring

**Files:**
- Create: `backend\src\swifthire\voice\models.py`, `backend\src\swifthire\voice\routes.py`, `backend\src\swifthire\voice\rubric.py`, `backend\tests\voice\test_interview.py`
- Create: `frontend\src\features\voice\LiveInterviewPage.tsx`, `frontend\src\features\voice\LiveInterviewPage.test.tsx`

**Interfaces:**
- Consumes: verified provider contract from Task 1 and stage workflow from Phase 3.
- Produces: candidate consent and start endpoint, provider session, completion endpoint, transcript, and `InterviewResult(score_percentage: int, criteria: list[CriterionResult], summary: str)`; store no raw audio by default.

- [ ] **Step 1: Write failing tests** — consent required, provider error not scored, incomplete session not marked complete, result schema rejects accent/emotion/personality criteria, and only role rubric evidence is persisted.
- [ ] **Step 2: Run `uv run pytest tests/voice/test_interview.py -q`** — expected: voice records/routes are absent.
- [ ] **Step 3: Implement interview lifecycle and live voice UI** — show AI disclosure, consent, connection state, end/retry state, and transcript availability; never auto-advance the candidate.
- [ ] **Step 4: Run backend/frontend voice tests** — expected: fake provider completes full consent-to-result flow with no credentials exposed.
- [ ] **Step 5: Commit** — `feat: add live AI voice interview` with the required Co-authored-by trailer.

### Task 3: Text accommodation path

**Files:**
- Create: `backend\src\swifthire\voice\text_interview.py`, `backend\tests\voice\test_text_interview.py`
- Modify: `frontend\src\features\voice\LiveInterviewPage.tsx`

**Interfaces:**
- Produces: the same job-specific rubric/result schema through a text interaction; candidate can select this path before starting an interview.

- [ ] **Step 1: Write failing tests** — text path uses the same role questions/rubric, preserves consent disclosure, and produces a recruiter-reviewable result without voice metrics.
- [ ] **Step 2: Run `uv run pytest tests/voice/test_text_interview.py -q`** — expected: text path is absent.
- [ ] **Step 3: Implement text alternative and UI selection** — keep live voice as the default path; do not penalize the alternative in scoring.
- [ ] **Step 4: Run all Phase 5 tests** — expected: voice and text paths complete into the same review workflow.
- [ ] **Step 5: Commit** — `feat: add text interview accommodation` with the required Co-authored-by trailer.
