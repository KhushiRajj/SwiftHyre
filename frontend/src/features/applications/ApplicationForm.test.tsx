import { fireEvent, render, screen } from '@testing-library/react';
import ApplicationForm from './ApplicationForm';

describe('ApplicationForm', () => {
  it('displays validation errors for incomplete or invalid submission', () => {
    render(<ApplicationForm />);

    fireEvent.click(screen.getByRole('button', { name: /submit application/i }));

    expect(screen.getByRole('alert')).toHaveTextContent('Please complete all fields.');

    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Jane Doe' } });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'jane@example.com' } });
    fireEvent.change(screen.getByLabelText(/cv upload/i), {
      target: { files: [new File(['not-a-pdf'], 'resume.txt', { type: 'text/plain' })] },
    });

    fireEvent.click(screen.getByRole('button', { name: /submit application/i }));
    expect(screen.getByRole('alert')).toHaveTextContent('Please upload a PDF file under 10 MiB.');
  });

  it('shows a loading state and a success message for a valid PDF upload', async () => {
    render(<ApplicationForm />);

    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Jane Doe' } });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'jane@example.com' } });
    fireEvent.change(screen.getByLabelText(/cv upload/i), {
      target: { files: [new File(['%PDF-1.4'], 'resume.pdf', { type: 'application/pdf' })] },
    });

    fireEvent.click(screen.getByRole('button', { name: /submit application/i }));

    expect(screen.getByRole('button', { name: /submitting/i })).toBeInTheDocument();
    expect(await screen.findByText(/application submitted/i)).toBeInTheDocument();
  });
});
