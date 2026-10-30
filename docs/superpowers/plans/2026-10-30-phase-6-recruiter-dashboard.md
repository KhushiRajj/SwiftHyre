# Phase 6 Recruiter Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an owner-scoped recruiter dashboard with truthful candidate and stage results, separate human decisions, and confirmed decision actions.

**Architecture:** Complete the existing Flask reporting endpoint by aggregating only result and workflow data available from current in-memory services, with explicit missing-result states and a public workflow decision-history accessor. Wire the existing React dashboard to the authenticated jobs list, dashboard endpoint, and existing job-scoped decision endpoint.

**Tech Stack:** Flask, Python, React, TypeScript, Vitest, React Testing Library, pytest.

**Spec:** [../specs/2026-10-30-phase-6-recruiter-dashboard-design.md](../specs/2026-10-30-phase-6-recruiter-dashboard-design.md)

## Global Constraints

- Use the existing modular React/TypeScript frontend and Flask backend.
- Follow `docs/superpowers/plans/2026-10-28-phase-6-recruiter-results-dashboard.md` for required endpoint shape, route behavior, and test coverage.
- Use the existing recruiter session for authentication and the Phase 3 workflow service for decisions.
- Treat the dashboard query as read-only; decision mutations remain delegated to the workflow service.
- Prefer existing domain services and explicit result schemas over accessing another service's private dictionaries.
- The codebase currently uses in-memory services; dashboard behavior is therefore prototype-only and not durable across process restarts.
- Keep phase-specific changes separable from the unrelated uncommitted assessment UI work.
- Do not translate absent, failed, or unavailable evidence into a zero score.
- Keep AI recommendations and recruiter decisions separate in API responses and UI.
- Exclude private CV storage details, provider credentials, browser session credentials, raw interview audio, and raw interview transcripts.
- Do not display a failed email notification as if a recruiter decision had been rolled back.
- Do not automatically advance or reject candidates based on model or assessment scores.

## Review Focus

- A job owned by another recruiter must return not found, and must not expose candidate rows or counts — test `test_dashboard_is_scoped_to_job_owner` in Task 1.
- An application with no recorded evidence, and a failed/unavailable result, must show a state with `score is None`; no fake zero or completed score — test `test_missing_and_failed_results_have_no_score` in Task 1 and `test_failed_and_pending_results_do_not_render_zero_scores` in Task 2.
- A rejected application or one with no valid current stage must not receive actionable decisions; scores must never determine actions — test `test_available_actions_follow_application_stage_and_status` in Task 1.
- Private CV/provider/session/audio/transcript values must not enter the dashboard response — test `test_dashboard_omits_private_artifacts` in Task 1.
- Decision confirmation must be cancelable; mutation failures must be visible, while success must refresh dashboard data and notification failures must not misstate the decision — test `test_decision_confirmation_failure_and_refresh` in Task 2.

---

### Task 1: Truthful owner-scoped dashboard API

**Files:**
- Modify: `backend/src/swifthire/__init__.py`
- Add: `backend/src/swifthire/reporting/__init__.py`
- Add: `backend/src/swifthire/reporting/routes.py`
- Modify: `backend/src/swifthire/reporting/schemas.py`
- Modify: `backend/src/swifthire/reporting/service.py`
- Modify: `backend/src/swifthire/workflow/service.py`
- Modify: `backend/tests/reporting/test_dashboard_api.py`
- Modify: `backend/tests/workflow/test_decisions.py`

**Interfaces:**
- Consumes: `get_job_service().get_by_id(job_id)`, `get_application_service().list_for_job(job_id)`, `get_assessment_service().get_application_assessments(application_id)`, `get_coding_service().list_for_job(job_id)`, `get_coding_service().get_submission_for_application(challenge_id, application_id)`, and `get_workflow_service()`.
- Produces: `ReportingService.get_job_dashboard(job_id: str, recruiter_id: str) -> dict | None`; `WorkflowService.list_decisions_for_application(application_id: str) -> list[ApplicationDecision]`; and the existing authenticated `GET /api/recruiter/jobs/<job_id>/dashboard` response.
- Retain the current dashboard response keys: `job`, `counts`, and `candidates`. Each candidate has `application_id`, `candidate_name`, `status`, `current_stage`, `match_result`, ordered `stage_results`, `decision_history`, `available_actions`, and `notification_states`.
- Result states are `pending`, `completed`, `failed`, `unavailable`, or `not_configured`; score is nullable and only populated for a completed result. Online-assessment results use submitted assessment scores. Coding results use submissions associated with challenges for this job; if multiple challenges are configured, their score is the arithmetic mean only after every challenge has a completed/partial scored submission. Any missing submission leaves the overall score null and state pending; provider failures yield unavailable and invalid submissions yield failed. Never expose source code or private test cases. Voice interview remains `not_configured` because no provider/result record exists.
- Match results remain `pending` with no score because applications do not persist a screening result. Do not run screening or invent a result while serving the read-only dashboard.
- Notification states are `not_applicable` where no notification record exists; do not infer `pending` or claim delivery without a record.
- Decision mutations remain on the existing `POST /api/recruiter/jobs/<job_id>/applications/<application_id>/decisions` route. Do not add a dashboard-specific decision endpoint.

- [ ] **Step 1: Add failing reporting tests** — extend `test_dashboard_api.py` with `test_missing_and_failed_results_have_no_score`, `test_completed_assessment_and_coding_results_are_aggregated`, `test_decisions_are_listed_without_private_workflow_access`, and `test_available_actions_follow_application_stage_and_status`. Add `test_list_decisions_for_application_returns_created_decisions_in_order` to `tests/workflow/test_decisions.py`. Assert missing assessment/coding results have explicit states and `score is None`; submitted assessment and completed/partial coding results expose only valid scores; failed/unavailable coding results do not expose scores; decision history is ordered and includes only recruiter decisions; rejected applications and applications without a configured current stage have no actions; and actions are based on stage/status rather than result scores. Keep the existing owner-scope, response-count, auth, privacy, and decision-route tests.
- [ ] **Step 2: Run focused backend tests to verify the gaps** — from `backend`, run `uv run pytest tests/reporting/test_dashboard_api.py tests/workflow/test_decisions.py -q`. Expected: new assertions fail against fabricated pending results/private dictionary access or missing decision accessor.
- [ ] **Step 3: Add a public workflow history accessor** — implement `WorkflowService.list_decisions_for_application(application_id: str) -> list[ApplicationDecision]` to return matching records ordered by `created_at`; update the dashboard to use this method instead of `_decisions_by_id`.
- [ ] **Step 4: Aggregate actual available result records** — update `ReportingService.get_job_dashboard(job_id: str, recruiter_id: str) -> dict | None` to return `None` for a missing/non-owned job, derive counts only from that job's applications, preserve `job.stage_order`, map assessment and coding records into explicit states, and use null scores unless a result is completed. If the job has multiple coding challenges, expose their arithmetic mean only after each configured challenge has a completed/partial scored submission; otherwise return a null overall score and pending/unavailable/failed state as applicable. Include no source, private challenge tests, CV data, provider secrets, browser credentials, or interview artifacts. Return match as pending/no-score and voice-interview as not configured until records exist. Set notification states to not_applicable unless a real delivery record is available.
- [ ] **Step 5: Derive safe available actions** — emit advance/reject actions only for non-rejected applications whose `current_stage` exists in the configured job stage order; use that current stage as `expected_stage`. Do not include an action for unknown/terminal application states, and do not inspect scores to decide actions.
- [ ] **Step 6: Run backend tests** — from `backend`, run `uv run pytest tests/reporting/test_dashboard_api.py tests/workflow/test_decisions.py -q`. Expected: focused tests pass, including owner scope, privacy, result states, and existing decision behavior.
- [ ] **Step 7: Commit the API task** — stage only the reporting package, its app registration, the workflow service and focused tests, plus this plan and its design spec; commit as `feat: complete recruiter dashboard reporting` with the required Co-authored-by trailer.

### Task 2: Wire dashboard into recruiter navigation and decisions

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/api.ts`
- Modify: `frontend/src/features/reporting/RecruiterDashboard.tsx`
- Modify: `frontend/src/features/reporting/RecruiterDashboard.test.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/features/jobs/JobListPage.tsx`
- Modify: `frontend/src/features/jobs/JobPages.test.tsx`
- Create: `frontend/src/features/reporting/RecruiterDashboardPage.tsx`
- Create: `frontend/src/features/reporting/RecruiterDashboardPage.test.tsx`

**Interfaces:**
- Consumes: `GET /api/recruiter/jobs` returning the authenticated recruiter's jobs; `GET /api/recruiter/jobs/<jobId>/dashboard`; and `POST /api/recruiter/jobs/<jobId>/applications/<applicationId>/decisions` with JSON `{decision, expected_stage}`.
- Produces: `requestJson<T>(url: string, init?: RequestInit): Promise<T>` in `frontend/src/api.ts`, which includes session credentials and throws the API's error message on failure; a recruiter jobs route at `/recruiter/jobs`; a results route at `/recruiter/jobs/<jobId>/results`; and a page that loads, retries, submits confirmed decisions, and refreshes after a successful mutation. Keep the existing unauthenticated/public/coding routes functional.
- Keep result states visible in text; do not show absent scores as zero. Render recommendation and recruiter-decision sections separately. Render no action buttons unless the API returns `available_actions`.
- `RecruiterDashboard` receives `onDecision(applicationId: string, decision: 'advance' | 'reject', expectedStage: string): Promise<void>`. It retains confirmation until the request succeeds, shows a rejected promise as an alert, and disables that candidate's decision actions while the request is pending.
- A failed decision request stays visible and does not trigger a success refresh; a successful decision refreshes dashboard data. Notification status is informational and does not change the displayed recruiter decision.

- [ ] **Step 1: Add failing UI tests** — extend `RecruiterDashboard.test.tsx` with `test_failed_and_pending_results_do_not_render_zero_scores`, `test_decision_buttons_follow_available_actions`, and `test_decision_confirmation_failure_and_refresh`; add `RecruiterDashboardPage.test.tsx` tests for dashboard loading/error/retry and request payload/path. Extend `JobPages.test.tsx` with `test_job_list_links_to_results` and `App.test.tsx` with `test_recruiter_routes_load_jobs_and_dashboard`. Assert explicit result state labels and no `0%` for null scores; no action for absent API actions; cancel sends no request; confirm sends the job-scoped path and `{decision, expected_stage}`; errors stay visible; success triggers a refetch; a failed notification is not presented as a failed recruiter decision; `/recruiter/jobs` loads the recruiter job list; and a job-list link opens its results route. Assert root and auth entry pages link to the recruiter job list.
- [ ] **Step 2: Run focused frontend tests to verify the gaps** — from `frontend`, run `npm test -- --run RecruiterDashboard JobPages App`. Expected: new API page, App route, and job-list integration tests fail before implementation.
- [ ] **Step 3: Share authenticated JSON requests and expose routes** — move the current `requestJson<T>` helper from `App.tsx` to `frontend/src/api.ts`, preserving `credentials: 'include'` and API error extraction; update existing App call sites to import it. Add discoverable recruiter-job links to the root and auth route. Wire `/recruiter/jobs` to fetch the authenticated jobs endpoint and render a Results link for each job; wire `/recruiter/jobs/<jobId>/results` to render `RecruiterDashboardPage`. Preserve existing route precedence and public/coding routes.
- [ ] **Step 4: Add the dashboard page data lifecycle** — implement `RecruiterDashboardPage` to fetch the selected job dashboard, show loading/error/retry states, submit decisions to the existing job-scoped endpoint, display mutation errors, and refetch after a successful response using `requestJson`.
- [ ] **Step 5: Complete result and decision presentation** — update `RecruiterDashboard` to label pending/failed/unavailable/not-configured/completed states, show available score/evidence/summary only, preserve distinct recommendation and recruiter decision sections, and require confirm/cancel before invoking a returned action. Retain confirmation on rejected `onDecision`, display the failure, and disable actions while pending. Keep failed notifications separate from decision outcomes.
- [ ] **Step 6: Run focused frontend tests** — from `frontend`, run `npm test -- --run RecruiterDashboard JobPages App`. Expected: all dashboard, API lifecycle, confirmation, App route, and job-list integration tests pass.
- [ ] **Step 7: Verify the full application** — from `backend`, run `uv run pytest -q`; from `frontend`, run `npm test -- --run` and `npm run build`. Expected: all tests pass and the production TypeScript/Vite build succeeds without changing unrelated generated or assessment files.
- [ ] **Step 8: Commit the UI task** — stage only the dashboard, jobs navigation, app route, and related tests; commit as `feat: add recruiter results dashboard UI` with the required Co-authored-by trailer.
