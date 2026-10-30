import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import RecruiterDashboard from './RecruiterDashboard';

function dashboardWithCandidate(availableActions: Array<{ decision: string; expected_stage: string }> = []) {
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
          { stage_key: 'coding_assessment', state: 'failed', score: null, criteria: [], summary: null },
          { stage_key: 'voice_interview', state: 'not_configured', score: null, criteria: [], summary: null },
        ],
        decision_history: [],
        available_actions: availableActions,
        notification_states: { online_assessment: 'failed' },
      },
    ],
  };
}

describe('RecruiterDashboard', () => {
  it('shows loading and retry states', () => {
    const { rerender } = render(<RecruiterDashboard loading />);
    expect(screen.getByText(/loading results/i)).toBeInTheDocument();

    rerender(<RecruiterDashboard error="Request failed" onRetry={() => {}} />);
    expect(screen.getByText(/request failed/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('renders empty state and keeps absent scores out of the UI', () => {
    const dashboard = {
      job: { id: 'job-1', title: 'Senior Designer', status: 'published' },
      counts: { total: 0, by_status: {} },
      candidates: [],
    };

    const { rerender } = render(<RecruiterDashboard dashboard={dashboard} />);
    expect(screen.getByText(/no candidates yet/i)).toBeInTheDocument();

    rerender(
      <RecruiterDashboard
        dashboard={{
          job: { id: 'job-1', title: 'Senior Designer', status: 'published' },
          counts: { total: 1, by_status: { pending: 1 } },
          candidates: [
            {
              application_id: 'app-1',
              candidate_name: 'Jane Candidate',
              status: 'pending',
              current_stage: 'online_assessment',
              match_result: { state: 'pending', score: null, criteria: [], summary: null },
              stage_results: [{ stage_key: 'online_assessment', state: 'pending', score: null, criteria: [], summary: null }],
              decision_history: [],
              available_actions: [],
              notification_states: { online_assessment: 'pending' },
            },
          ],
        }}
      />
    );

    expect(screen.getByText('Jane Candidate')).toBeInTheDocument();
    expect(screen.queryByText('0%')).not.toBeInTheDocument();
  });

  it('separates the AI recommendation from the recruiter decision', () => {
    render(
      <RecruiterDashboard
        dashboard={{
          job: { id: 'job-1', title: 'Senior Designer', status: 'published' },
          counts: { total: 1, by_status: { pending: 1 } },
          candidates: [
            {
              application_id: 'app-1',
              candidate_name: 'Jane Candidate',
              status: 'pending',
              current_stage: 'online_assessment',
              match_result: {
                state: 'completed',
                score: 84,
                criteria: [{ name: 'Product sense', score: 84, evidence: 'Strong design rationale', summary: 'Strong fit' }],
                summary: 'Strong fit for the role.',
              },
              stage_results: [
                {
                  stage_key: 'online_assessment',
                  state: 'completed',
                  score: 76,
                  criteria: [{ name: 'Written response', score: 76, evidence: 'Clear and structured answers', summary: 'Solid but not perfect' }],
                  summary: 'Solid but not perfect',
                },
              ],
              decision_history: [{ decision: 'advance', expected_stage: 'online_assessment', timestamp: '2026-01-01' }],
              available_actions: [{ decision: 'reject', expected_stage: 'online_assessment' }],
              notification_states: { online_assessment: 'sent' },
            },
          ],
        }}
      />
    );

    expect(screen.getByText(/ai recommendation/i)).toBeInTheDocument();
    expect(screen.getByText(/recruiter decision/i)).toBeInTheDocument();
    expect(screen.getByText(/strong fit for the role/i)).toBeInTheDocument();
    expect(screen.getByText(/advance/i)).toBeInTheDocument();
    expect(screen.getByText(/sent/i)).toBeInTheDocument();
  });

  it('allows confirmation before posting a decision', () => {
    render(
      <RecruiterDashboard
        dashboard={{
          job: { id: 'job-1', title: 'Senior Designer', status: 'published' },
          counts: { total: 1, by_status: { pending: 1 } },
          candidates: [
            {
              application_id: 'app-1',
              candidate_name: 'Jane Candidate',
              status: 'pending',
              current_stage: 'online_assessment',
              match_result: { state: 'pending', score: null, criteria: [], summary: null },
              stage_results: [],
              decision_history: [],
              available_actions: [{ decision: 'advance', expected_stage: 'online_assessment' }],
              notification_states: { online_assessment: 'pending' },
            },
          ],
        }}
        onDecision={async () => {}}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /advance/i }));
    expect(screen.getByRole('button', { name: /confirm advance/i })).toBeInTheDocument();
  });

  it('renders explicit result states without inventing a zero score', () => {
    render(<RecruiterDashboard dashboard={dashboardWithCandidate()} />);

    expect(screen.getByText(/online assessment: pending/i)).toBeInTheDocument();
    expect(screen.getByText(/coding assessment: failed/i)).toBeInTheDocument();
    expect(screen.getByText(/voice interview: not configured/i)).toBeInTheDocument();
    expect(screen.queryByText('0%')).not.toBeInTheDocument();
  });

  it('shows only available actions and keeps confirmation after a failed decision', async () => {
    const onDecision = vi.fn().mockRejectedValue(new Error('Decision conflict.'));
    render(
      <RecruiterDashboard
        dashboard={dashboardWithCandidate([{ decision: 'reject', expected_stage: 'online_assessment' }])}
        onDecision={onDecision}
      />,
    );

    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Advance' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reject' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Reject' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Decision conflict.');
    expect(screen.getByRole('button', { name: 'Confirm Reject' })).toBeInTheDocument();
    expect(onDecision).toHaveBeenCalledWith('app-1', 'reject', 'online_assessment');
  });

  it('cancels a decision without sending a mutation', () => {
    const onDecision = vi.fn();
    render(
      <RecruiterDashboard
        dashboard={dashboardWithCandidate([{ decision: 'advance', expected_stage: 'online_assessment' }])}
        onDecision={onDecision}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Advance' }));
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(onDecision).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Advance' })).toBeInTheDocument();
  });

  it('disables decision actions while the confirmed request is pending', async () => {
    let resolveDecision!: () => void;
    const onDecision = vi.fn(() => new Promise<void>((resolve) => {
      resolveDecision = resolve;
    }));
    render(
      <RecruiterDashboard
        dashboard={dashboardWithCandidate([{ decision: 'advance', expected_stage: 'online_assessment' }])}
        onDecision={onDecision}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Advance' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Advance' }));
    expect(screen.getByRole('button', { name: 'Confirm Advance' })).toBeDisabled();

    resolveDecision();
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Confirm Advance' })).not.toBeInTheDocument();
    });
  });

  it('keeps failed notification status separate from recruiter decisions', () => {
    render(<RecruiterDashboard dashboard={dashboardWithCandidate()} />);

    const notifications = screen.getByRole('heading', { name: 'Notifications' }).parentElement;
    const decisions = screen.getByRole('heading', { name: 'Recruiter decision' }).parentElement;
    expect(notifications).toHaveTextContent('online_assessment: failed');
    expect(decisions).toHaveTextContent('No recruiter decisions yet.');
  });
});
