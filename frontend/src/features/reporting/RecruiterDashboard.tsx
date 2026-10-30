import { useState } from 'react';

type Criterion = {
  name: string;
  score?: number | null;
  evidence?: string;
  summary?: string | null;
};

type ResultState = 'pending' | 'completed' | 'failed' | 'unavailable' | 'not_configured';

type MatchResult = {
  state?: ResultState;
  score?: number | null;
  criteria?: Criterion[];
  summary?: string | null;
};

type StageResult = {
  stage_key: string;
  state: ResultState;
  score?: number | null;
  criteria?: Criterion[];
  summary?: string | null;
};

type Candidate = {
  application_id: string;
  candidate_name: string;
  status: string;
  current_stage?: string | null;
  match_result?: MatchResult;
  stage_results?: StageResult[];
  decision_history?: Array<{ decision: string; expected_stage: string; timestamp?: string }>;
  available_actions?: Array<{ decision: 'advance' | 'reject'; expected_stage: string }>;
  notification_states?: Record<string, string>;
};

export type Dashboard = {
  job: { id: string; title: string; status: string };
  counts: { total: number; by_status: Record<string, number> };
  candidates: Candidate[];
};

type RecruiterDashboardProps = {
  loading?: boolean;
  error?: string;
  dashboard?: Dashboard;
  onRetry?: () => void;
  onDecision?: (
    applicationId: string,
    decision: 'advance' | 'reject',
    expectedStage: string,
  ) => Promise<void>;
};

function formatDecisionLabel(decision: string) {
  return decision.charAt(0).toUpperCase() + decision.slice(1);
}

function formatLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/\b[a-z]/g, (letter) => letter.toUpperCase());
}

function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score == null) return null;

  return <strong>{score}%</strong>;
}

export default function RecruiterDashboard({
  loading = false,
  error,
  dashboard,
  onRetry,
  onDecision,
}: RecruiterDashboardProps) {
  const [pendingDecision, setPendingDecision] = useState<{
    applicationId: string;
    decision: 'advance' | 'reject';
    expectedStage: string;
  } | null>(null);
  const [decisionError, setDecisionError] = useState('');
  const [submittingDecision, setSubmittingDecision] = useState(false);

  const confirmDecision = async () => {
    if (!pendingDecision || !onDecision) return;

    setDecisionError('');
    setSubmittingDecision(true);
    try {
      await onDecision(
        pendingDecision.applicationId,
        pendingDecision.decision,
        pendingDecision.expectedStage,
      );
      setPendingDecision(null);
    } catch (error) {
      setDecisionError(error instanceof Error ? error.message : 'The decision could not be saved.');
    } finally {
      setSubmittingDecision(false);
    }
  };

  if (loading) {
    return <section><p role="status">Loading results...</p></section>;
  }

  if (error) {
    return (
      <section>
        <p role="alert">{error}</p>
        {onRetry ? <button type="button" onClick={onRetry}>Retry</button> : null}
      </section>
    );
  }

  const candidates = dashboard?.candidates ?? [];

  return (
    <main>
      <header>
        <h1>{dashboard?.job?.title ?? 'Recruiter dashboard'}</h1>
        <p>{dashboard?.counts?.total ?? 0} candidates</p>
      </header>

      {candidates.length === 0 ? (
        <p>No candidates yet.</p>
      ) : (
        candidates.map((candidate) => {
          const matchResult = candidate.match_result ?? { state: 'pending', score: null, criteria: [], summary: null };
          const stageResults = candidate.stage_results ?? [];
          const notificationStates = candidate.notification_states ?? {};
          const actions = candidate.available_actions ?? [];

          return (
            <article key={candidate.application_id}>
              <h2>{candidate.candidate_name}</h2>
              <p>Status: {candidate.status}</p>
              <p>Current stage: {candidate.current_stage ?? 'unassigned'}</p>

              <section>
                <h3>AI recommendation</h3>
                <p>State: {formatLabel(matchResult.state ?? 'pending')}</p>
                <ScoreBadge score={matchResult.score ?? null} />
                {matchResult.criteria && matchResult.criteria.length > 0 ? (
                  <ul>
                    {matchResult.criteria.map((criterion) => (
                      <li key={`${candidate.application_id}-${criterion.name}`}>
                        <strong>{criterion.name}</strong>
                        <ScoreBadge score={criterion.score} />
                        <p>{criterion.evidence}</p>
                        <small>{criterion.summary ?? criterion.evidence}</small>
                      </li>
                    ))}
                  </ul>
                ) : null}
                {matchResult.summary ? <p>{matchResult.summary}</p> : null}
              </section>

              <section>
                <h3>Stage results</h3>
                {stageResults.length > 0 ? (
                  <ul>
                    {stageResults.map((stage) => (
                      <li key={`${candidate.application_id}-${stage.stage_key}`}>
                        <strong>{formatLabel(stage.stage_key)}</strong>
                        <p>{formatLabel(stage.stage_key)}: {formatLabel(stage.state)}</p>
                        <ScoreBadge score={stage.score ?? null} />
                        <p>{stage.summary ?? 'No summary yet.'}</p>
                        {stage.criteria && stage.criteria.length > 0 ? (
                          <ul>
                            {stage.criteria.map((criterion) => (
                              <li key={`${candidate.application_id}-${stage.stage_key}-${criterion.name}`}>
                                <strong>{criterion.name}</strong>
                                <ScoreBadge score={criterion.score} />
                                <p>{criterion.evidence}</p>
                                {criterion.summary ? <small>{criterion.summary}</small> : null}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No stage results yet.</p>
                )}
              </section>

              <section>
                <h3>Recruiter decision</h3>
                {candidate.decision_history && candidate.decision_history.length > 0 ? (
                  <ul>
                    {candidate.decision_history.map((decision, index) => (
                      <li key={`${candidate.application_id}-decision-${index}`}>
                        {formatDecisionLabel(decision.decision)} — {formatLabel(decision.expected_stage)}
                        {decision.timestamp ? ` (${decision.timestamp})` : ''}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No recruiter decisions yet.</p>
                )}

                {actions.length > 0 ? (
                  <div>
                    {actions.map((action) => {
                      const isConfirming =
                        pendingDecision &&
                        pendingDecision.applicationId === candidate.application_id &&
                        pendingDecision.decision === action.decision &&
                        pendingDecision.expectedStage === action.expected_stage;

                      if (isConfirming) {
                        return (
                          <span key={`${candidate.application_id}-${action.decision}`}>
                            <p>Confirm {formatDecisionLabel(action.decision)} for {candidate.candidate_name}?</p>
                            <button
                              type="button"
                              disabled={submittingDecision}
                              onClick={() => { void confirmDecision(); }}
                            >
                              Confirm {formatDecisionLabel(action.decision)}
                            </button>
                            <button
                              type="button"
                              disabled={submittingDecision}
                              onClick={() => {
                                setPendingDecision(null);
                                setDecisionError('');
                              }}
                            >
                              Cancel
                            </button>
                          </span>
                        );
                      }

                      return (
                        <button
                          key={`${candidate.application_id}-${action.decision}`}
                          type="button"
                          disabled={submittingDecision}
                          onClick={() =>
                            setPendingDecision({
                              applicationId: candidate.application_id,
                              decision: action.decision,
                              expectedStage: action.expected_stage,
                            })
                          }
                        >
                          {formatDecisionLabel(action.decision)}
                        </button>
                      );
                    })}
                  </div>
                ) : null}
                {decisionError ? <p role="alert">{decisionError}</p> : null}
              </section>

              <section>
                <h3>Notifications</h3>
                {Object.entries(notificationStates).length > 0 ? (
                  <ul>
                    {Object.entries(notificationStates).map(([stage, state]) => (
                      <li key={`${candidate.application_id}-notification-${stage}`}>
                        {stage}: {state}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No notifications.</p>
                )}
              </section>
            </article>
          );
        })
      )}
    </main>
  );
}
