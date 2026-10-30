# SwiftHyre

SwiftHyre is a recruiter-focused hiring platform with recruiter-managed jobs,
candidate applications, assessments, and review workflows. The prototype uses
in-memory service stores; it is not production-ready or persistent yet.

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

## Coding assessment execution

Candidate code is sent only from the Flask backend to OnlineCompiler.io; SwiftHyre
does not execute candidate code in the Flask process. Set `ONLINECOMPILER_API_KEY`
in the backend environment to enable execution. Without a key, submissions remain
visible as `unavailable` and receive no score, so they can be retried after setup.
The REST API key must remain server-side.

Recruiters can sign in or register at `/auth`, then use the challenge editor at
`/recruiter/jobs/<job-id>/coding-challenges`. Candidates can open
`/jobs/<public-job-slug>/coding-challenges`, choose a challenge, and enter the
coding-assessment token from their invitation. During Vite development, `/api`
requests are proxied to the Flask server at `http://127.0.0.1:5000`.

As checked on 2026-10-30, OnlineCompiler.io's official pages state that its Free
plan includes 100,000 runs per month and commercial use. Its API documents a
100 KB source/input limit, up to 30 seconds per run, 512 MB memory, and 46
language runtimes. This adapter currently maps Python, JavaScript, TypeScript,
Java, C, C++, C#, Go, Rust, PHP, and Ruby. SwiftHyre limits a challenge to eight
private cases; each private case is a separate API run.

References: [API authentication and endpoints](https://onlinecompiler.io/docs),
[execution limits and usage](https://onlinecompiler.io/docs/limits),
[compiler IDs](https://onlinecompiler.io/docs/compilers), and
[sandbox and data handling](https://onlinecompiler.io/security).

The provider states that execution history includes submitted code, input,
output, errors, timing, API key, and client IP. Obtain appropriate candidate
disclosure/consent and review the provider's current retention and privacy terms
before production use. Provider access and the no-cost allowance have not been
smoke-tested from this repository because no API key is configured.
