import { render, screen } from '@testing-library/react';
import ApplicationReviewPage from './ApplicationReviewPage';

describe('ApplicationReviewPage', () => {
  it('shows AI recommendation evidence for a submitted application', () => {
    render(
      <ApplicationReviewPage
        application={{
          id: 'app-1',
          applicant_name: 'Jane Candidate',
          email: 'jane@example.com',
          status: 'pending',
          screening: {
            score: 84,
            criteria: [{ name: 'Product leadership', score: 84, evidence: 'Led roadmap planning', reason: 'Strong strategic fit' }],
            summary: 'Strong fit for the role.',
            status: 'ok',
          },
        }}
      />,
    );

    expect(screen.getByText(/ai recommendation/i)).toBeInTheDocument();
    expect(screen.getByText('84')).toBeInTheDocument();
    expect(screen.getByText(/product leadership/i)).toBeInTheDocument();
    expect(screen.getByText(/led roadmap planning/i)).toBeInTheDocument();
    expect(screen.getByText(/strong fit for the role/i)).toBeInTheDocument();
  });
});
