type PublicJob = {
  title: string;
  description: string;
  status: 'draft' | 'published' | 'closed';
};

export default function PublicJobPage({ job }: { job: PublicJob }) {
  return (
    <main>
      <h1>{job.title}</h1>
      <p>{job.description}</p>
    </main>
  );
}
