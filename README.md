# SwiftHyre

SwiftHyre is a recruiter-focused hiring platform. This repository currently includes the Phase 1 foundation: a Flask backend with a health endpoint and a React + Vite frontend shell.

## Local development

### Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e . pytest
python -m pytest tests/test_health.py -q
```

### Frontend

```bash
cd frontend
npm install
npm test -- --run
```

### Local Postgres

```bash
docker compose up -d postgres
```

Copy `.env.example` to `.env` and adjust local values before running the full application stack.
