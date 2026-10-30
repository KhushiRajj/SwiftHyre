import { useCallback, useEffect, useState } from 'react';
import { requestJson } from '../../api';
import RecruiterDashboard, { type Dashboard } from './RecruiterDashboard';

type Decision = 'advance' | 'reject';

export default function RecruiterDashboardPage({ jobId }: { jobId: string }) {
  const [dashboard, setDashboard] = useState<Dashboard>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [decisionNotice, setDecisionNotice] = useState('');

  const loadDashboard = useCallback(async (): Promise<boolean> => {
    setLoading(true);
    setError('');
    try {
      const result = await requestJson<Dashboard>(`/api/recruiter/jobs/${jobId}/dashboard`);
      setDashboard(result);
      return true;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not load recruiter results.');
      return false;
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const submitDecision = async (
    applicationId: string,
    decision: Decision,
    expectedStage: string,
  ) => {
    setDecisionNotice('');
    await requestJson(`/api/recruiter/jobs/${jobId}/applications/${applicationId}/decisions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, expected_stage: expectedStage }),
    });

    const refreshed = await loadDashboard();
    if (!refreshed) {
      setDecisionNotice('Decision saved, but results could not be refreshed.');
    }
  };

  return (
    <>
      <p><a href="/recruiter/jobs">Back to jobs</a></p>
      {decisionNotice ? <p role="status">{decisionNotice}</p> : null}
      <RecruiterDashboard
        dashboard={dashboard}
        loading={loading}
        error={error}
        onRetry={() => { void loadDashboard(); }}
        onDecision={submitDecision}
      />
    </>
  );
}
