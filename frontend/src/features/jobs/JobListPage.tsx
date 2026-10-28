type JobSummary = {
  id: string;
  title: string;
  status: 'draft' | 'published' | 'closed';
};

export default function JobListPage({ jobs }: { jobs: JobSummary[] }) {
  return (
    <main>
      <h1>Jobs</h1>
      <ul>
        {jobs.map((job) => (
          <li key={job.id}>
            {job.title} ({job.status})
          </li>
        ))}
      </ul>
    </main>
  );
}
