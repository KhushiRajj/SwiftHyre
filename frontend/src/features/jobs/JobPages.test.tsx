import { fireEvent, render, screen } from '@testing-library/react';
import JobEditor from './JobEditor';
import PublicJobPage from './PublicJobPage';
import JobListPage from './JobListPage';

describe('Job workflows', () => {
  it('shows validation errors in the job editor', () => {
    render(<JobEditor />);

    fireEvent.click(screen.getByRole('button', { name: 'Save job' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Title and description are required.');
  });

  it('includes stage configuration fields for progression decisions', () => {
    render(<JobEditor />);

    expect(screen.getByLabelText(/stage order/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/recommendation threshold/i)).toBeInTheDocument();
  });

  it('renders a published public job page', () => {
    render(
      <PublicJobPage
        job={{
          title: 'Senior Product Designer',
          description: 'Design product experiences.',
          status: 'published',
        }}
      />
    );

    expect(screen.getByRole('heading', { name: 'Senior Product Designer' })).toBeInTheDocument();
    expect(screen.getByText('Design product experiences.')).toBeInTheDocument();
  });

  it('links each recruiter job to its results dashboard', () => {
    render(
      <JobListPage
        jobs={[{ id: 'job-123', title: 'Senior Product Designer', status: 'published' }]}
      />,
    );

    expect(screen.getByRole('link', { name: 'Results for Senior Product Designer' }))
      .toHaveAttribute('href', '/recruiter/jobs/job-123/results');
  });
});
