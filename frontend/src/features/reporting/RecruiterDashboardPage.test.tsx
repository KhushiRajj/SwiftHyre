import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import RecruiterDashboardPage from './RecruiterDashboardPage';

function response(body: unknown, status = 200): Response {
  return {
    ok: status < 400,
    status,
    json: async () => body,
  } as Response;
}

function dashboard(availableActions: Array<{ decision: string; expected_stage: string }> = []) {
  return {
    job: { id: 'job-1', title: 'Senior Designer', status: 'published' },
    counts: { total: 1, by_status: { pending: 1 } },
    candidates: [
      {
        application_id: 'app-1',
        candidate_name: 'Jane Candidate',
        status: 'pending',
        current_stage: 'online_assessment',
        match_result: { state: 'pending', score: null, criteria: [], summary: null },
        stage_results: [
          { stage_key: 'online_assessment', state: 'pending', score: null, criteria: [], summary: null },
        ],
        decision_history: [],
        available_actions: availableActions,
        notification_states: { online_assessment: 'failed' },
      },
    ],
  };
}

describe('RecruiterDashboardPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads the dashboard and retries a failed request', async () => {
    const fetchMock = vi.spyOn(window, 'fetch')
      .mockResolvedValueOnce(response({ error: 'Temporary failure.' }, 500))
      .mockResolvedValueOnce(response(dashboard()));

    render(<RecruiterDashboardPage jobId="job-1" />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading results...');
    expect(await screen.findByRole('alert')).toHaveTextContent('Temporary failure.');
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(await screen.findByText('Jane Candidate')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/recruiter/jobs/job-1/dashboard',
      expect.objectContaining({ credentials: 'include' }),
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('posts confirmed decisions and refreshes only after success', async () => {
    const fetchMock = vi.spyOn(window, 'fetch')
      .mockResolvedValueOnce(response(dashboard([{ decision: 'advance', expected_stage: 'online_assessment' }])))
      .mockResolvedValueOnce(response({ error: 'Decision conflict.' }, 409))
      .mockResolvedValueOnce(response({ decision: 'advance', expected_stage: 'online_assessment' }, 201))
      .mockResolvedValueOnce(response(dashboard()));

    render(<RecruiterDashboardPage jobId="job-1" />);
    expect(await screen.findByText('Jane Candidate')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Advance' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Advance' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Decision conflict.');
    expect(fetchMock).toHaveBeenCalledTimes(2);
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Advance' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/recruiter/jobs/job-1/applications/app-1/decisions',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({ decision: 'advance', expected_stage: 'online_assessment' }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      '/api/recruiter/jobs/job-1/applications/app-1/decisions',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      '/api/recruiter/jobs/job-1/dashboard',
      expect.objectContaining({ credentials: 'include' }),
    );
  });
});
