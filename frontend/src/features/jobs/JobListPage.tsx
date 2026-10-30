export type JobSummary = {
  id: string;
  title: string;
  status: 'draft' | 'published' | 'closed';
};

export default function JobListPage({ jobs }: { jobs: JobSummary[] }) {
  return (
    <main>
      <h1>Jobs</h1>
      {jobs.length === 0 ? <p>No jobs yet.</p> : null}
      <ul>
        {jobs.map((job) => (
          <li key={job.id}>
            {job.title} ({job.status})
            {' '}
            <a href={`/recruiter/jobs/${job.id}/results`}>Results for {job.title}</a>
          </li>
        ))}
      </ul>
    </main>
  );
}
