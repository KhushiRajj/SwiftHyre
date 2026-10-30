# SwiftHyre Hiring Platform — Design

## Intent

SwiftHyre helps small hiring teams run a structured hiring process without
needing a large recruiting operation. Recruiters create a vacancy and share a
link; candidates apply and complete role-relevant assessment stages; recruiters
review the evidence and decide who advances. The system keeps each round's
results and communications together in a recruiter dashboard.

## Goals

- Let recruiters register, sign in, create vacancies with job descriptions,
  and share a public application link.
- Let candidates apply through that link and submit a PDF CV.
- Extract CV text with PyMuPDF and produce a job-related match assessment with
  traceable evidence for recruiter review.
- Support an online assessment, a coding assessment using the OnlineCompiler.io
  API, and a live, two-way AI voice HR interview.
- Use AI to assist with screening, assessment, interview, and result summaries.
  Keep the AI work divided into focused roles and return structured results.
- Require recruiter approval before every candidate advancement or rejection;
  send the corresponding email notifications with Resend.
- Give recruiters a dashboard to review candidate status and per-round scores,
  evidence, and summaries.

## Non-goals

- Making final employment decisions or automatically advancing/rejecting
  candidates based on model output.
- Replacing a full applicant tracking, payroll, or employee-management system.
- Video interviewing; the agreed HR experience is live voice.
- A general-purpose autonomous agent platform.

## Anti-goals and safeguards

- No opaque AI-only pass/fail decisions. Show evidence and scores for human
  review, and record recruiter decisions separately from AI recommendations.
- Do not infer or score protected or irrelevant traits. Voice evaluation should
  assess role-relevant answers against a disclosed rubric, not accent, emotion,
  personality, or other proxies.
- Do not silently fail when document extraction, an AI provider, email, or an
  assessment integration fails; surface a retryable error/status to recruiters.
- Do not store provider credentials in source code or expose them to the
  browser. Keep candidate files and interview data private and access-controlled.

## Approaches considered

1. **Modular React + Flask application (chosen).** A single application
   deployment with focused backend modules for jobs, applications, screening,
   assessments, interviews, and reporting. Integrations sit behind small
   interfaces. This supports a coherent first release and keeps operational
   overhead low while preserving clear AI-agent boundaries.
2. **Distributed agent services.** Run each hiring stage as a separate service
   coordinated by a queue. This isolates long-running work and can scale
   independently, but adds deployment, coordination, and failure-handling
   complexity before workload needs are known.

The modular approach was chosen to deliver the complete recruiter/candidate
workflow first. Focused AI roles and provider interfaces retain room to grow
without requiring a distributed system at launch.

For AI and voice, use hosted cloud APIs with usable free tiers; do not require
local model runtimes. For other services, use open-source/local components or
hosted free tiers where practical. Free-tier quotas, service terms, and
deployment costs must be checked before launch; "free" does not promise
production capacity or zero hosting costs.

## User experience and workflow

1. A recruiter creates an account, signs in, creates a vacancy, and shares its
   application URL.
2. A candidate opens the URL, submits contact details and a PDF CV, and receives
   confirmation. The service extracts the CV text and creates an explainable
   job-match recommendation.
3. The recruiter reviews the application and match evidence in the dashboard.
   The recruiter explicitly approves or declines the candidate; the system
   emails the candidate about the decision.
4. For each approved next stage, the platform sends an invitation and records
   results for the online assessment, coding assessment, or live AI voice
   interview. Stage sequence and thresholds are owned by the vacancy, with
   recruiter approval required to move a candidate forward or reject them.
5. Recruiters review each candidate's stage history, scores, evidence, and
   AI-generated summaries before making the next decision.

## Technical direction

- **Frontend:** React recruiter dashboard and candidate application/assessment
  flows.
- **Backend:** Python with Flask; a modular HTTP API owns authentication,
  vacancy/application lifecycle, candidate progression, and integrations.
- **Database:** PostgreSQL for users, vacancies, applications, stage state,
  assessment results, recruiter decisions, and communication status.
- **Account scope:** Individual recruiter accounts only for the first release;
  no shared organizations, team membership, or recruiter roles.
- **CVs:** PyMuPDF extracts text from PDF uploads. Use Cloudinary only within
  an available no-cost tier, or a local/S3-compatible open-source storage
  adapter such as MinIO. Store files privately. Check PyMuPDF's licensing terms
  for the intended commercial use; use a permissively licensed PDF library
  instead if its terms do not fit.
- **Email:** Keep Resend behind an email adapter and use it only within an
  available no-cost tier. Mailpit can capture email locally during development.
  Production delivery limits and deliverability must be verified; do not claim
  reliable production email without a configured delivery service.
- **Coding assessment:** Use the OnlineCompiler.io API only if its current
  access and quotas fit the no-cost target. Keep a provider interface so a
  self-hosted open-source Judge0 deployment can be substituted. Never execute
  untrusted candidate code directly in the Flask application; provider
  failures must be visible and must not be interpreted as candidate failures.
- **AI:** Focused, bounded tasks for CV matching, assessment support, live
  interviewing, and result summaries. Model output is structured and stored
  separately from human decisions. Use hosted cloud model APIs only when their
  current free tier and terms meet the need. Keep a provider boundary rather
  than assuming Groq, Google AI Studio, or OpenRouter has a suitable free tier.
- **Voice:** A live conversation needs speech recognition, speech generation,
  and a low-latency model. Use a hosted cloud voice/speech service only if its
  free tier supports the complete live interaction. Do not silently substitute
  a local model or a paid service if no suitable tier exists; surface the
  limitation and defer that integration pending an approved alternative.
  Confirm the full voice path meets latency, candidate-consent, and privacy
  needs before treating it as production-ready.
- **Agent framework:** The user has not selected Microsoft Agent Framework or
  LangChain. Begin with focused role modules and structured inputs/outputs;
  adopt a framework only if a concrete orchestration need justifies it.

## Constraints and open implementation decisions

- Build on an otherwise empty repository (currently README-only).
- Exact authentication mechanism, candidate identity/return flow, assessment
  content, and retention policy remain implementation decisions; choose
  conventional, privacy-conscious defaults and document them.
- **Launch region:** India. Confirm applicable privacy, hiring, and AI-related
  requirements before production use; obtain appropriate candidate disclosures
  and consent for voice interviews and external processing.
- The AI/voice cost target depends on currently available cloud free tiers and
  their quotas. If a necessary provider has no usable free tier, identify the
  limitation and defer that integration rather than silently introducing a
  local model or paid dependency.
- Hosted integrations require service access and credentials provided outside
  source control.
- The product needs a text alternative or equivalent accommodation path for
  candidates who cannot use voice; implement this without changing the agreed
  live-voice default.
- No production credentials or external service accounts were provided.

## Left to the builder

Choose the initial deployment layout, API shapes, schema, authentication
approach, background-task mechanism, assessment format, cloud voice and LLM
providers with usable free tiers, and test strategy. Keep the first vertical
slice small but end-to-end, make external integrations replaceable, verify
current no-cost terms before selecting hosted services, and document any
assumptions that affect candidate experience, hiring decisions, or cost.
