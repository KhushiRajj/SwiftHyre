# SwiftHyre Phase 6: Recruiter Results Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give recruiters one owner-scoped dashboard to review candidate progress, stage results, evidence, summaries, notifications, and human decisions.

**Architecture:** Add a read-only reporting service over the persisted job, application, screening, assessment, interview, notification, and decision records. Expose one recruiter-authorized job dashboard API and render its explicit result states in React; route advance/reject actions through the Phase 3 decision service.

**Tech Stack:** React, TypeScript, Flask, PostgreSQL, pytest, Vitest, React Testing Library.

**Spec:** [../specs/2026-10-28-swifthire-design.md](../specs/2026-10-28-swifthire-design.md)

## Global Constraints

- **Give recruiters a dashboard to review candidate status and per-round scores, evidence, and summaries.**
- **Require recruiter approval before every candidate advancement or rejection; send the corresponding email notifications with Resend.**
- **No opaque AI-only pass/fail decisions. Show evidence and scores for human review, and record recruiter decisions separately from AI recommendations.**
- **Do not store provider credentials in source code or expose them to the browser. Keep candidate files and interview data private and access-controlled.**
- **Account scope: Individual recruiter accounts only for the first release; no shared organizations, team membership, or recruiter roles.**

## Review Focus

- Candidates belonging to another recruiter must never appear in dashboard rows or aggregate counts — test `test_dashboard_is_scoped_to_job_owner` in Task 1.
- Missing, failed, or unavailable round results must have an explicit state and no synthetic zero score — test `test_stage_result_states_do_not_invent_scores` in Task 1.
- AI recommendations and recruiter decisions must remain separate in the API and UI — test `test_dashboard_preserves_recommendations_and_decisions` in Task 1 and `test_recommendation_is_distinct_from_recruiter_decision` in Task 2.
- Empty jobs and candidates with partial stage history must render usable states — test `test_empty_and_partial_dashboard_states` in Task 2.
- Private CV object keys/URLs, provider credentials, browser session credentials, and raw interview audio/transcripts must not be included in the dashboard payload — test `test_dashboard_omits_private_artifacts` in Task 1.

---

### Task 1: Owner-scoped dashboard API

**Files:**
- Create: `backend\src\swifthire\reporting\schemas.py`
- Create: `backend\src\swifthire\reporting\service.py`
- Create: `backend\src\swifthire\reporting\routes.py`
- Create: `backend\tests\reporting\test_dashboard_api.py`
- Modify: `backend\src\swifthire\workflow\routes.py`

**Interfaces:**
- Consumes: Phase 1-5 job, application, match, stage-result, notification, and recruiter-decision records; authenticated recruiter identity; Phase 3 `decide(application_id: UUID, recruiter_id: UUID, decision: Literal["advance", "reject"], expected_stage: str) -> ApplicationDecision` service for decision mutations.
- Produces: `get_job_dashboard(job_id: UUID, recruiter_id: UUID) -> JobDashboard | None`; authenticated `GET /api/recruiter/jobs/<uuid:job_id>/dashboard`; and recruiter decision action route `POST /api/recruiter/applications/<uuid:application_id>/decisions` with JSON fields `decision` (`advance|reject`) and `expected_stage`.
- `JobDashboard` contains `job` (`id`, `title`, `status`), `counts` (`total: int`, `by_status: dict[str, int]`), and `candidates`. Each candidate has `application_id: UUID`, `candidate_name`, `status`, `current_stage`, `match_result`, ordered `stage_results`, `decision_history`, `available_actions`, and `notification_states`.
- `match_result` exposes `state` (`pending|completed|failed|unavailable`), nullable `score` (0-100 only when completed), `criteria` (each with `name`, nullable 0-100 `score`, and `evidence`), and nullable `summary`. Each stage result uses the same fields plus `stage_key` (`online_assessment|coding_assessment|voice_interview`) and may use `not_configured` as its state. `available_actions` is a list of `{decision: "advance"|"reject", expected_stage: string}`. Decision history contains only recruiter decisions, with decision, stage, and timestamp. Notification states use `pending|sent|failed|not_applicable`, keyed by stage.
- The dashboard is read-only. Its query and counts must scope through the owning job and authenticated recruiter. A job not owned by that recruiter returns 404; unauthenticated requests return 401. Decision actions delegate to the Phase 3 service and never infer or change a decision from scores.
- Dashboard payloads must not include CV object keys/URLs, provider credentials or browser session credentials, raw interview audio, or raw interview transcripts.

- [ ] **Step 1: Write failing API tests** — add named tests `test_dashboard_requires_recruiter_auth`, `test_dashboard_is_scoped_to_job_owner`, `test_dashboard_counts_only_returned_candidates`, `test_stage_result_states_do_not_invent_scores`, `test_completed_results_include_score_evidence_and_summary`, `test_dashboard_preserves_recommendations_and_decisions`, `test_available_actions_follow_workflow_not_scores`, `test_dashboard_omits_private_artifacts`, and `test_decision_action_delegates_to_phase3_service`. Assert unauthenticated 401; cross-owner job 404; owner A sees only owner A applications, `counts.total == len(candidates)`, and `sum(counts.by_status.values()) == counts.total`; pending/failed/unavailable results have `score is None` rather than `0`; completed results include a 0-100 score, criteria evidence, and summary; recruiter decisions and available actions are serialized independently of match recommendations; secret test values for CV keys/URLs, provider/session credentials, audio, and transcripts are absent from the serialized response; and a valid decision request forwards only its application, recruiter, decision, and expected stage to the Phase 3 service while preserving its conflict/error response.
- [ ] **Step 2: Run the focused API tests** — from `backend`, run `uv run pytest tests/reporting/test_dashboard_api.py -q`. Expected: tests fail because the reporting modules and dashboard route are not implemented.
- [ ] **Step 3: Implement result schemas and owner-scoped aggregation** — add typed response schemas and a service that joins the Phase 1-5 persisted records for one owned job, preserves configured stage order, represents absent/failed results explicitly, and excludes private artifacts. Do not create a new persisted score or mutate workflow state while building a dashboard response.
- [ ] **Step 4: Add the dashboard and decision routes** — resolve recruiter identity from the existing session; return 401/404 as specified; serialize only the dashboard DTO; add the decision action route to `workflow/routes.py`, forward it to the Phase 3 decision service, and return its validation/conflict errors without adding dashboard-specific decision logic.
- [ ] **Step 5: Run reporting and workflow API tests** — from `backend`, run `uv run pytest tests/reporting/test_dashboard_api.py tests/workflow/test_decisions.py -q`. Expected: dashboard and existing decision tests pass, including owner isolation and human-only decision transitions.
- [ ] **Step 6: Commit** — `feat: add recruiter results API` with the required Co-authored-by trailer.

### Task 2: Recruiter results dashboard UI

**Files:**
- Create: `frontend\src\features\reporting\RecruiterDashboard.tsx`
- Create: `frontend\src\features\reporting\CandidateResults.tsx`
- Create: `frontend\src\features\reporting\RecruiterDashboard.test.tsx`
- Modify: `frontend\src\features\jobs\JobListPage.tsx`
- Modify: `frontend\src\features\jobs\JobPages.test.tsx`

**Interfaces:**
- Consumes: `GET /api/recruiter/jobs/<jobId>/dashboard`, the existing recruiter session/API client, and the Phase 3 decision action route.
- Produces: a vacancy-level dashboard reachable from the owning recruiter’s job list. Render candidate status/current stage, match recommendation with evidence and summary, ordered stage scores/evidence/summaries, notification states, and a distinct recruiter decision history. Show advance/reject actions only when returned in `available_actions`.
- Decision buttons require explicit confirmation, submit `decision` and `expected_stage`, disable while pending, show mutation failures without implying success, and reload the dashboard after success. A failed email notification is displayed separately from the successful recruiter decision and does not imply that the decision was rolled back. No candidate file URLs, object keys, raw transcripts, or audio are rendered.

- [ ] **Step 1: Write failing dashboard tests** — add named tests `test_dashboard_loading_and_retryable_error`, `test_empty_and_partial_dashboard_states`, `test_failed_and_pending_results_do_not_render_zero_scores`, `test_recommendation_is_distinct_from_recruiter_decision`, and `test_decision_requires_confirmation_and_refreshes`; extend `JobPages.test.tsx` to assert the owning recruiter can open the selected job’s dashboard. Assert loading and retry states; a clear empty-job state; usable rows when some rounds are pending/failed; no `0%` for absent scores; separately labeled AI recommendation and recruiter decision; visible evidence, summary, and notification state; decision actions appear only when present in `available_actions`; canceling confirmation sends no mutation; confirming sends the expected decision/stage; mutation errors remain visible; a failed notification remains distinct from the committed decision; and a successful decision refreshes the dashboard.
- [ ] **Step 2: Run the focused frontend tests** — from `frontend`, run `npm test -- --run RecruiterDashboard JobPages`. Expected: the new dashboard and job-list integration tests fail before implementation.
- [ ] **Step 3: Implement the candidate results view and dashboard** — use accessible headings, status text, and labeled score/evidence sections; render each result according to its explicit state; provide fetch error/retry handling; keep recommendations and decisions in separate UI sections.
- [ ] **Step 4: Integrate with the recruiter job list and decision flow** — add a results entry point for each job and render the selected job’s dashboard; wire confirmation to the Phase 3 decision route and refresh after success; display failed notification delivery separately so it is clear the decision succeeded but the email needs attention.
- [ ] **Step 5: Run focused frontend and reporting tests** — from `frontend`, run `npm test -- --run RecruiterDashboard JobPages`; from `backend`, run `uv run pytest tests/reporting/test_dashboard_api.py tests/workflow/test_decisions.py -q`. Expected: all affected tests pass, the dashboard displays only authorized job results, and decisions remain recruiter-controlled.
- [ ] **Step 6: Commit** — `feat: add recruiter results dashboard` with the required Co-authored-by trailer.
