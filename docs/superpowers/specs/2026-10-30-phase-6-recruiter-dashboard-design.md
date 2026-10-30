# SwiftHyre Phase 6: Recruiter Results Dashboard Design

## Intent

Give each recruiter a usable, owner-scoped view of candidate progress for a
vacancy. Recruiters should be able to inspect available screening and stage
evidence, see notification and decision history, and make explicit human
decisions without interpreting missing results as failures.

## Why now

The repository already has a Phase 6 plan, an initial reporting API/service,
dashboard components, and API/UI tests. The dashboard component is not
connected to the application, and the reporting service currently returns
placeholder match/stage/notification data rather than aggregating available
records. The remaining work is to complete the planned reporting behavior and
make the recruiter review surface reachable and actionable.

## Goals

- Complete the recruiter-authorized, job-owner-scoped dashboard API.
- Aggregate existing candidate application, match/screening, assessment,
  coding, interview, notification, and recruiter-decision results where they
  exist.
- Preserve the configured stage order and explicitly represent pending,
  failed, unavailable, or unconfigured results without inventing scores.
- Keep AI recommendations and recruiter decisions separate in API responses
  and UI.
- Exclude private CV storage details, provider credentials, browser session
  credentials, raw interview audio, and raw interview transcripts.
- Add a recruiter job-list entry point to the selected job's dashboard.
- Require confirmation for advance/reject, show pending/error states, and
  refresh after a successful decision.
- Show notification delivery state separately from a committed recruiter
  decision.
- Preserve unrelated uncommitted work in the existing checkout.

## Non-goals

- Completing recruiter invitation and candidate online-assessment UI flows;
  that is a separate follow-up after the dashboard.
- Implementing the Phase 5 live voice interview provider or changing its
  retention behavior.
- Replacing the prototype's in-memory stores with PostgreSQL persistence.
- Changing job creation, application screening, coding execution, or recruiter
  authentication except where direct dashboard integration requires it.
- Automatically advancing or rejecting candidates based on model or
  assessment scores.

## Anti-goals and safeguards

- Do not leak data from jobs owned by another recruiter, including aggregate
  counts.
- Do not translate absent, failed, or unavailable evidence into a zero score.
- Do not infer recruiter intent from AI recommendations or candidate scores.
- Do not include CV object keys/URLs, provider/session credentials, raw audio,
  or raw transcripts in dashboard payloads.
- Do not display a failed email notification as if a recruiter decision had
  been rolled back.
- Do not stage, rewrite, or discard unrelated dirty-checkout changes.

## Approaches considered

1. **Dashboard first — selected.** Follow the existing Phase 6 plan, complete
   the reporting API and dashboard UI, and wire confirmation-based decisions.
   This uses the existing implementation/tests and gives recruiters a usable
   review surface before candidate assessment pages are completed. The
   trade-off is that recruiter invitations and candidate online-quiz screens
   remain incomplete until a later task.
2. **Assessment flow first.** Wire recruiter invitations and the candidate
   online quiz before returning to reporting. This completes the candidate
   facing stage sooner, but leaves the dashboard's reporting data as
   placeholders, so recruiters cannot review a coherent result.
3. **One stage end-to-end.** Join invitation, candidate completion, result
   review, and recruiter decision into one workflow before expanding to other
   stages. This produces the most cohesive journey and exposes integration
   gaps early, but broadens the current task across more APIs and UI surfaces
   than the existing Phase 6 plan.

The user selected dashboard-first because it follows the repository's existing
Phase 6 plan and stabilizes the recruiter review surface. The assessment UI is
deferred to a separate follow-up.

## Constraints and implementation direction

- Use the existing modular React/TypeScript frontend and Flask backend.
- Follow `docs/superpowers/plans/2026-10-28-phase-6-recruiter-results-dashboard.md`
  for required endpoint shape, route behavior, and test coverage.
- Use the existing recruiter session for authentication and the Phase 3
  workflow service for decisions.
- Treat the dashboard query as read-only; decision mutations remain delegated
  to the workflow service.
- Prefer existing domain services and explicit result schemas over accessing
  another service's private dictionaries.
- The codebase currently uses in-memory services; dashboard behavior is
  therefore prototype-only and not durable across process restarts.
- Keep phase-specific changes separable from the unrelated uncommitted
  assessment UI work.

## Success criteria

- Owner isolation and counts are verified by backend tests.
- Completed, pending, failed, unavailable, and unconfigured results are
  represented accurately, with only genuine completed scores displayed.
- Recommendations and recruiter decisions remain distinct in API and UI.
- Sensitive candidate/provider artifacts are absent from serialized responses.
- Recruiters can open a job dashboard, confirm or cancel a decision, see
  failures without false success, and see the dashboard refresh after success.
- Focused backend and frontend suites, followed by the full project suites and
  production build, pass.

## Builder decisions

- Where underlying Phase 1-5 result records are not yet implemented, expose an
  explicit pending or not-configured state rather than synthesizing data.
- Keep the dashboard limited to data currently available through existing
  services; do not introduce new persistence or provider integrations.
- Decide concrete component boundaries and accessible interaction details
  during planning, following the current React patterns.
