# SwiftHyre Phase 1: Recruiter Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a working recruiter account and vacancy workflow with shareable public job pages.

**Architecture:** Start a React/TypeScript frontend and modular Flask API backed by PostgreSQL. Use SQLAlchemy models and migrations, cookie-based recruiter sessions, and individual ownership for every vacancy.

**Tech Stack:** React, TypeScript, Vite, Flask, Flask-SQLAlchemy, Flask-Migrate, PostgreSQL, pytest, Vitest, React Testing Library.

**Spec:** [../specs/2026-10-28-swifthire-design.md](../specs/2026-10-28-swifthire-design.md)

## Global Constraints

- **Account scope:** Individual recruiter accounts only for the first release; no shared organizations, team membership, or recruiter roles.
- **Launch region:** India.
- **For AI and voice, use hosted cloud APIs with usable free tiers; do not require local model runtimes.**
- **Do not store provider credentials in source code or expose them to the browser.**
- **Require recruiter approval before every candidate advancement or rejection.**
- **Build on an otherwise empty repository (currently README-only).**

## Review Focus

- Duplicate registrations and invalid credentials must not create sessions — test registration/login validation in Task 2.
- A recruiter must not read or modify another recruiter's vacancy — test owner-scoped API access in Task 3.
- Draft/closed vacancies must not be publicly discoverable — test public job route in Task 3.
- Missing/invalid configuration must fail visibly rather than return success-shaped health — test startup/config validation in Task 1.
- Session cookies must not be readable by browser scripts and must be cleared on logout — test cookie attributes and logout in Task 2.

---

### Task 1: Project and service foundation

**Files:**
- Create: `backend\pyproject.toml`, `backend\src\swifthire\__init__.py`, `backend\src\swifthire\config.py`, `backend\src\swifthire\extensions.py`
- Create: `frontend\package.json`, `frontend\src\main.tsx`, `frontend\src\App.tsx`
- Create: `compose.yaml`, `.env.example`, `.gitignore`
- Modify: `README.md`
- Test: `backend\tests\test_health.py`, `frontend\src\App.test.tsx`

**Interfaces:**
- Produces: Flask `create_app(config_overrides: dict | None = None) -> Flask`; `GET /api/health` returns `{"status":"ok"}` only when app config loads; Vite renders the SwiftHyre shell.

- [ ] **Step 1: Write failing backend and frontend smoke tests** — assert `GET /api/health` returns HTTP 200 and the exact JSON, and the React shell renders the `SwiftHyre` heading.
- [ ] **Step 2: Run tests to verify they fail** — `cd backend; uv run pytest tests/test_health.py -q` and `cd frontend; npm test -- --run`; expected: missing app/test targets.
- [ ] **Step 3: Implement project bootstrap** — configure Flask factory, PostgreSQL URL from environment, React/Vite test scripts, and a local PostgreSQL service; document local setup in README and do not add production secrets.
- [ ] **Step 4: Run both smoke tests** — expected: both pass from their respective project directories.
- [ ] **Step 5: Commit** — `feat: bootstrap SwiftHyre application` with the required Co-authored-by trailer.

### Task 2: Recruiter registration and sessions

**Files:**
- Create: `backend\src\swifthire\auth\models.py`, `backend\src\swifthire\auth\routes.py`, `backend\src\swifthire\auth\service.py`, `backend\tests\auth\test_auth_routes.py`
- Create: `frontend\src\api\client.ts`, `frontend\src\features\auth\AuthPage.tsx`, `frontend\src\features\auth\AuthPage.test.tsx`

**Interfaces:**
- Consumes: `create_app()` and shared SQLAlchemy extension from Task 1.
- Produces: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`; recruiter identity is stored in an HttpOnly, SameSite=Lax session cookie.

- [ ] **Step 1: Write failing tests** — cover valid registration/login, duplicate email (409), invalid credentials (401), unauthenticated `/me` (401), and logout clearing the session cookie.
- [ ] **Step 2: Run `uv run pytest tests/auth/test_auth_routes.py -q`** — expected: failures because auth routes/models are absent.
- [ ] **Step 3: Implement account model and routes** — normalize email, hash passwords with Werkzeug's password helpers, use CSRF protection for state-changing session requests, and set Secure cookies in production.
- [ ] **Step 4: Add auth form tests and run backend/frontend tests** — expected: valid form submission reaches authenticated state; validation errors are visible; all Task 1-2 tests pass.
- [ ] **Step 5: Commit** — `feat: add recruiter authentication` with the required Co-authored-by trailer.

### Task 3: Vacancy management and public job pages

**Files:**
- Create: `backend\src\swifthire\jobs\models.py`, `backend\src\swifthire\jobs\routes.py`, `backend\src\swifthire\jobs\service.py`, `backend\tests\jobs\test_job_routes.py`
- Create: `frontend\src\features\jobs\JobListPage.tsx`, `frontend\src\features\jobs\JobEditor.tsx`, `frontend\src\features\jobs\PublicJobPage.tsx`, `frontend\src\features\jobs\JobPages.test.tsx`
- Create: `backend\migrations\versions\<generated migration>`

**Interfaces:**
- Consumes: recruiter session and database from Tasks 1-2.
- Produces: `POST /api/recruiter/jobs`, `GET /api/recruiter/jobs`, `GET /api/recruiter/jobs/<id>`, `PATCH /api/recruiter/jobs/<id>`, and `GET /api/public/jobs/<slug>`. Job fields: `title`, `description`, `status` (`draft|published|closed`), `public_slug`.

- [ ] **Step 1: Write failing route/UI tests** — assert required title/description, unique public slug, owner-only access, draft/closed public 404, and published job public view.
- [ ] **Step 2: Run `uv run pytest tests/jobs/test_job_routes.py -q` and `npm test -- --run JobPages`** — expected: failures because jobs are absent.
- [ ] **Step 3: Implement models, migration, owner-scoped routes, and recruiter job forms** — publish changes status only after validation; use opaque random public slugs.
- [ ] **Step 4: Run all Phase 1 tests and apply migrations to PostgreSQL** — expected: all tests pass and a recruiter can create, publish, and open a vacancy link.
- [ ] **Step 5: Commit** — `feat: add recruiter vacancy workflow` with the required Co-authored-by trailer.
