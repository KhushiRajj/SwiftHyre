# SwiftHyre Phase 3: Candidate Progression and Online Assessment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give recruiters explicit control over candidate stage decisions and let candidates complete a job-related online assessment.

**Architecture:** Model configurable stages and auditable recruiter decisions in PostgreSQL. Send stage links through an email adapter; generate draft multiple-choice tests with a cloud model, require recruiter review, and score submitted answers deterministically.

**Tech Stack:** Flask, PostgreSQL, React, hosted cloud LLM free tier, Resend free tier if available, Mailpit for local email, pytest, Vitest.

**Spec:** [../specs/2026-10-28-swifthire-design.md](../specs/2026-10-28-swifthire-design.md)

## Global Constraints

- **Require recruiter approval before every candidate advancement or rejection; send the corresponding email notifications with Resend.**
- **For AI and voice, use hosted cloud APIs with usable free tiers; do not require local model runtimes.**
- **Model output is structured and stored separately from human decisions.**
- **Do not silently fail when an AI provider or email integration fails; surface a retryable error/status to recruiters.**
- **Hosted integrations require service access and credentials provided outside source control.**

## Review Focus

- Stale or repeated recruiter decisions must not advance a candidate twice — test transition idempotency in Task 1.
- A candidate must not access another candidate's assessment using a guessed ID — test opaque invitation tokens in Task 2.
- Correct answers must never be sent to the candidate before submission — test response payloads in Task 2.
- Provider/email outages must not count as assessment failure or success — test status and retry behavior in Tasks 1-2.
- AI-generated questions must be reviewed before candidates receive them — test publication gate in Task 2.

---

### Task 1: Vacancy stages and human-approved decisions

**Files:**
- Create: `backend\src\swifthire\workflow\models.py`, `backend\src\swifthire\workflow\service.py`, `backend\src\swifthire\workflow\routes.py`, `backend\tests\workflow\test_decisions.py`
- Modify: `backend\src\swifthire\jobs\models.py`, `frontend\src\features\jobs\JobEditor.tsx`

**Interfaces:**
- Consumes: jobs and applications from Phases 1-2.
- Produces: vacancy stage configuration with ordered stage keys `online_assessment`, `coding_assessment`, `voice_interview` and optional `recommendation_threshold` (0-100); decision service `decide(application_id: UUID, recruiter_id: UUID, decision: Literal["advance","reject"], expected_stage: str) -> ApplicationDecision`. A threshold may label a result as a recommendation only; it never changes candidate state.

- [ ] **Step 1: Write failing tests** — cover configured stage order and threshold, recruiter-only advance/reject, invalid transition (409), another recruiter (404), threshold-based recommendation without a state change, and a repeated request with the same idempotency key producing one decision event.
- [ ] **Step 2: Run `uv run pytest tests/workflow/test_decisions.py -q`** — expected: workflow model/service is absent.
- [ ] **Step 3: Implement stage state and decision audit** — never derive a human decision from an AI score; require a fresh recruiter action for each stage.
- [ ] **Step 4: Run decision and job-editor tests** — expected: stages can be configured per vacancy and only valid manual decisions change state.
- [ ] **Step 5: Commit** — `feat: add recruiter-controlled candidate progression` with the required Co-authored-by trailer.

### Task 2: Email invitations and reviewed online assessment

**Files:**
- Create: `backend\src\swifthire\notifications\base.py`, `backend\src\swifthire\notifications\resend.py`, `backend\src\swifthire\assessments\models.py`, `backend\src\swifthire\assessments\service.py`, `backend\tests\assessments\test_online_assessment.py`
- Create: `frontend\src\features\assessments\AssessmentEditor.tsx`, `frontend\src\features\assessments\CandidateAssessmentPage.tsx`, `frontend\src\features\assessments\AssessmentPages.test.tsx`
- Modify: `backend\src\swifthire\workflow\service.py`

**Interfaces:**
- Consumes: stage decision service from Task 1; cloud AI provider adapter from Phase 2.
- Produces: `EmailSender.send(to: str, subject: str, text: str, idempotency_key: str) -> SendResult`; application confirmation and recruiter-approved 10-question multiple-choice draft; candidate invitation uses a random, single-application stage token; score is integer percentage from 0 to 100.

- [ ] **Step 1: Write failing tests** — assert successful application sends a confirmation, model returns exactly 10 valid questions, recruiter must approve before invite, candidate API omits answer keys, each token is candidate/stage-scoped and single-use, score percentage is deterministic, and email outage leaves a retryable notification status.
- [ ] **Step 2: Run `uv run pytest tests/assessments/test_online_assessment.py -q`** — expected: assessment and notification contracts are absent.
- [ ] **Step 3: Implement email adapter and quiz flow** — use Mailpit locally; configure Resend only after confirming current free-tier terms. Store answer keys server-side; never auto-advance on a score.
- [ ] **Step 4: Run backend/frontend assessment tests** — expected: candidates can complete an approved quiz once and recruiters see its result; failed email delivery remains visible.
- [ ] **Step 5: Commit** — `feat: add emailed online assessments` with the required Co-authored-by trailer.
