# SwiftHyre Phase 2: Candidate Applications and CV Screening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let candidates submit PDF CVs to published jobs and give recruiters an evidence-based AI match recommendation.

**Architecture:** Add a public application API, private object storage adapter, PyMuPDF extraction, and a cloud-model adapter that returns validated structured screening results. Keep model output separate from recruiter decisions.

**Tech Stack:** React, Flask, PostgreSQL, PyMuPDF (subject to commercial license review), MinIO or an eligible Cloudinary free tier, pytest, Vitest.

**Spec:** [../specs/2026-10-28-swifthire-design.md](../specs/2026-10-28-swifthire-design.md)

## Global Constraints

- **Store files privately and keep candidate files and interview data private and access-controlled.**
- **For AI and voice, use hosted cloud APIs with usable free tiers; do not require local model runtimes.**
- **No opaque AI-only pass/fail decisions. Show evidence and scores for human review, and record recruiter decisions separately from AI recommendations.**
- **Do not infer or score protected or irrelevant traits.**
- **Do not store provider credentials in source code or expose them to the browser.**

## Review Focus

- Invalid, oversized, encrypted, or non-PDF uploads must be rejected with a clear error — test in Task 1.
- A storage or extraction outage must not create an apparently complete application — test transactional failure handling in Task 1.
- Malformed or unavailable model output must not become a zero score or rejection — test in Task 2.
- Resume matching must not score protected/irrelevant traits — test prompt/schema contract and sanitized inputs in Task 2.
- Candidate resume contents must not be retrievable from a public URL — test access control in Task 1.

---

### Task 1: Candidate application and private CV storage

**Files:**
- Create: `backend\src\swifthire\applications\models.py`, `backend\src\swifthire\applications\routes.py`, `backend\src\swifthire\applications\service.py`
- Create: `backend\src\swifthire\storage\base.py`, `backend\src\swifthire\storage\minio.py`, `backend\src\swifthire\storage\cloudinary.py`, `backend\tests\applications\test_submission.py`
- Create: `frontend\src\features\applications\ApplicationForm.tsx`, `frontend\src\features\applications\ApplicationForm.test.tsx`

**Interfaces:**
- Consumes: published job lookup from Phase 1.
- Produces: `POST /api/public/jobs/<slug>/applications` accepts `name`, `email`, and `cv` multipart fields; `CVStorage.save(file: BinaryIO, content_type: str) -> StoredObject`; `StoredObject` contains private `object_key`, `content_type`, and `size_bytes`.

- [ ] **Step 1: Write failing tests** — verify valid PDF creates one application, unpublished job returns 404, non-PDF or file larger than 10 MiB returns 400, and storage failure leaves no application record.
- [ ] **Step 2: Run `uv run pytest tests/applications/test_submission.py -q`** — expected: missing route, model, and storage adapter failures.
- [ ] **Step 3: Implement application persistence and private storage** — MinIO is the local default; add Cloudinary only after its current no-cost terms are confirmed. Keep object keys private and never return them as public URLs.
- [ ] **Step 4: Add candidate form tests and run Task 1 tests** — assert accessible labels, upload validation, loading state, and a clear completion message; expected: all pass.
- [ ] **Step 5: Commit** — `feat: add candidate job applications` with the required Co-authored-by trailer.

### Task 2: CV extraction and explainable match recommendation

**Files:**
- Create: `backend\src\swifthire\screening\extractor.py`, `backend\src\swifthire\screening\matcher.py`, `backend\src\swifthire\screening\schemas.py`, `backend\tests\screening\test_screening.py`
- Modify: `backend\src\swifthire\applications\service.py`
- Create: `backend\src\swifthire\ai\base.py`, `backend\src\swifthire\ai\cloud_provider.py`

**Interfaces:**
- Consumes: application/job records from Task 1 and configured cloud model provider.
- Produces: `ResumeExtractor.extract(pdf_bytes: bytes) -> str`; `ResumeMatcher.match(job_description: str, resume_text: str) -> MatchResult`; `MatchResult(score: int, criteria: list[CriterionResult], summary: str)` with score 0-100 and per-criterion evidence/reason.

- [ ] **Step 1: Write failing tests** — valid text PDF extracts text; unreadable/encrypted PDF records extraction failure; schema rejects out-of-range scores/missing evidence; provider timeout is shown as `screening_failed`, never as score zero.
- [ ] **Step 2: Run `uv run pytest tests/screening/test_screening.py -q`** — expected: screening code and typed result schema are absent.
- [ ] **Step 3: Implement PyMuPDF extraction and cloud adapter** — configure provider URL/model/key only through environment; test with a fake provider. Verify a suitable free-tier cloud model and PyMuPDF licensing before enabling production processing.
- [ ] **Step 4: Run screening tests** — expected: match results include only job-related criteria and traceable evidence; failure states remain reviewable and retryable.
- [ ] **Step 5: Commit** — `feat: add explainable resume screening` with the required Co-authored-by trailer.

### Task 3: Recruiter application review

**Files:**
- Create: `backend\src\swifthire\applications\recruiter_routes.py`, `backend\tests\applications\test_review.py`
- Create: `frontend\src\features\applications\ApplicationReviewPage.tsx`, `frontend\src\features\applications\ApplicationReviewPage.test.tsx`

**Interfaces:**
- Consumes: application and `MatchResult` from Tasks 1-2.
- Produces: recruiter-only list/detail APIs scoped to the owning job, including extraction/screening status and evidence; no API in this phase may advance or reject a candidate automatically.

- [ ] **Step 1: Write failing tests** — assert owner-only access, visible pending/failed screening state, and display of score, criteria, evidence, and summary.
- [ ] **Step 2: Run backend and frontend review tests** — expected: route and UI tests fail before implementation.
- [ ] **Step 3: Implement review endpoints and page** — label model output as recommendation, not recruiter decision; add retry action only for retryable extraction/matching failures.
- [ ] **Step 4: Run all Phase 2 tests** — expected: candidate can apply and an owning recruiter can review the application without public access to the CV.
- [ ] **Step 5: Commit** — `feat: add recruiter application review` with the required Co-authored-by trailer.
