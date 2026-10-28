type ScreeningResult = {
  score: number | null;
  criteria: Array<{ name: string; score: number; evidence: string; reason: string }>;
  summary: string;
  status: 'ok' | 'screening_failed';
};

type Application = {
  id: string;
  applicant_name: string;
  email: string;
  status: string;
  screening?: ScreeningResult;
};

export default function ApplicationReviewPage({ application }: { application: Application }) {
  const screening = application.screening ?? {
    score: null,
    criteria: [],
    summary: 'No screening result yet.',
    status: 'screening_failed',
  };

  return (
    <section>
      <h2>Application review</h2>
      <p>{application.applicant_name}</p>
      <p>{application.email}</p>
      <p>AI recommendation</p>
      <strong>{screening.score ?? '—'}</strong>
      {screening.criteria.length > 0 ? (
        <ul>
          {screening.criteria.map((criterion) => (
            <li key={criterion.name}>
              <h3>{criterion.name}</h3>
              <p>{criterion.evidence}</p>
            </li>
          ))}
        </ul>
      ) : null}
      <p>{screening.summary}</p>
    </section>
  );
}
