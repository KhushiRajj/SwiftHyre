import { useCallback, useEffect, useState } from 'react';
import CandidateCodingPage from './features/coding/CandidateCodingPage';
import ChallengeEditor from './features/coding/ChallengeEditor';
import AuthPage from './features/auth/AuthPage';
import { requestJson } from './api';
import JobListPage, { type JobSummary } from './features/jobs/JobListPage';
import RecruiterDashboardPage from './features/reporting/RecruiterDashboardPage';

type PublicChallenge = {
  id: string;
  title: string;
  prompt: string;
  allowed_languages: string[];
  public_test_cases: Array<{ input: string; expected_output: string }>;
};

type SubmissionResponse = {
  status: string;
  score?: number;
  message?: string;
};

function RecruiterChallengeRoute({ jobId }: { jobId: string }) {
  const [saved, setSaved] = useState(false);

  return (
    <main>
      <h1>SwiftHyre</h1>
      <h2>Create coding challenge</h2>
      <ChallengeEditor
        onSave={async (challenge) => {
          await requestJson(`/api/recruiter/jobs/${jobId}/coding-challenges`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(challenge),
          });
          setSaved(true);
        }}
      />
      {saved ? <p role="status">Challenge saved.</p> : null}
    </main>
  );
}

function RecruiterAuthRoute() {
  return (
    <>
      <AuthPage
        onSubmit={async ({ mode, name, email, password }) => {
          await requestJson(mode === 'register' ? '/api/auth/register' : '/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(mode === 'register' ? { name, email, password } : { email, password }),
          });
        }}
      />
      <p><a href="/recruiter/jobs">Recruiter jobs</a></p>
    </>
  );
}

function RecruiterJobsRoute() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setJobs(await requestJson<JobSummary[]>('/api/recruiter/jobs'));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not load recruiter jobs.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  return (
    <>
      <p><a href="/">SwiftHyre home</a></p>
      {loading ? <p role="status">Loading jobs...</p> : null}
      {error ? (
        <section>
          <p role="alert">{error}</p>
          <button type="button" onClick={() => { void loadJobs(); }}>Retry</button>
        </section>
      ) : null}
      {!loading && !error ? <JobListPage jobs={jobs} /> : null}
    </>
  );
}

function CandidateChallengeRoute({ jobSlug }: { jobSlug: string }) {
  const [challenges, setChallenges] = useState<PublicChallenge[]>([]);
  const [selectedChallengeId, setSelectedChallengeId] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [submissionMessage, setSubmissionMessage] = useState('');
  const challenge = challenges.find((item) => item.id === selectedChallengeId);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError('');

    requestJson<PublicChallenge[]>(`/api/public/jobs/${jobSlug}/coding-challenges`)
      .then((items) => {
        if (active) {
          setChallenges(items);
          setSelectedChallengeId(items[0]?.id ?? '');
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setLoadError(error instanceof Error ? error.message : 'Could not load coding challenges.');
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [jobSlug]);

  return (
    <main>
      <h1>SwiftHyre</h1>
      <h2>Coding challenges</h2>
      {loading ? <p role="status">Loading coding challenges...</p> : null}
      {loadError ? <p role="alert">{loadError}</p> : null}
      {!loading && !loadError && challenges.length === 0
        ? <p>No coding challenges are available for this job.</p>
        : null}
      {challenges.length > 1 ? (
        <label htmlFor="coding-challenge">
          Challenge
          <select
            id="coding-challenge"
            value={selectedChallengeId}
            onChange={(event) => setSelectedChallengeId(event.target.value)}
          >
            {challenges.map((item) => (
              <option key={item.id} value={item.id}>{item.title}</option>
            ))}
          </select>
        </label>
      ) : null}
      {challenge ? (
        <CandidateCodingPage
          challenge={challenge}
          assessmentToken=""
          onSubmit={async (submission) => {
            const result = await requestJson<SubmissionResponse>(
              `/api/public/coding-challenges/${submission.challengeId}/submissions`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  assessment_token: submission.assessmentToken,
                  language: submission.language,
                  source: submission.source,
                }),
              },
            );
            setSubmissionMessage(result.message ?? (
              result.score === undefined
                ? `Submission status: ${result.status}.`
                : `Submission status: ${result.status}. Score: ${result.score}%.`
            ));
          }}
        />
      ) : null}
      {submissionMessage ? <p role="status">{submissionMessage}</p> : null}
    </main>
  );
}

export default function App() {
  if (window.location.pathname === '/auth') {
    return <RecruiterAuthRoute />;
  }

  if (window.location.pathname === '/recruiter/jobs' || window.location.pathname === '/recruiter/jobs/') {
    return <RecruiterJobsRoute />;
  }

  const resultsRoute = window.location.pathname.match(/^\/recruiter\/jobs\/([^/]+)\/results\/?$/);
  if (resultsRoute) {
    return <RecruiterDashboardPage jobId={resultsRoute[1]} />;
  }

  const recruiterRoute = window.location.pathname.match(
    /^\/recruiter\/jobs\/([^/]+)\/coding-challenges\/?$/,
  );
  if (recruiterRoute) {
    return <RecruiterChallengeRoute jobId={recruiterRoute[1]} />;
  }

  const candidateRoute = window.location.pathname.match(/^\/jobs\/([^/]+)\/coding-challenges\/?$/);
  if (candidateRoute) {
    return <CandidateChallengeRoute jobSlug={candidateRoute[1]} />;
  }

  return (
    <main>
      <h1>SwiftHyre</h1>
      <p><a href="/auth">Recruiter sign in or create an account</a></p>
      <p><a href="/recruiter/jobs">Recruiter jobs</a></p>
      <p>Recruiters can create coding challenges at /recruiter/jobs/&lt;job-id&gt;/coding-challenges.</p>
      <p>Candidates can open coding challenges at /jobs/&lt;public-job-slug&gt;/coding-challenges.</p>
    </main>
  );
}
