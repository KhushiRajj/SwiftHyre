import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import App from './App';

function response(body: unknown, status = 200): Response {
  return {
    ok: status < 400,
    status,
    json: async () => body,
  } as Response;
}

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.history.replaceState({}, '', '/');
  });

  it('renders the SwiftHyre heading', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'SwiftHyre' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Recruiter jobs' }))
      .toHaveAttribute('href', '/recruiter/jobs');
  });

  it('links authenticated recruiters to their jobs from the auth page', () => {
    window.history.pushState({}, '', '/auth');

    render(<App />);

    expect(screen.getByRole('link', { name: 'Recruiter jobs' }))
      .toHaveAttribute('href', '/recruiter/jobs');
  });

  it('loads recruiter jobs and a selected job dashboard', async () => {
    const fetchMock = vi.spyOn(window, 'fetch')
      .mockResolvedValueOnce(response([
        { id: 'job-123', title: 'Senior Product Designer', status: 'published' },
      ]))
      .mockResolvedValueOnce(response({
        job: { id: 'job-123', title: 'Senior Product Designer', status: 'published' },
        counts: { total: 0, by_status: {} },
        candidates: [],
      }));
    window.history.pushState({}, '', '/recruiter/jobs');

    const jobsPage = render(<App />);
    const resultsLink = await screen.findByRole('link', {
      name: 'Results for Senior Product Designer',
    });
    expect(resultsLink).toHaveAttribute('href', '/recruiter/jobs/job-123/results');
    jobsPage.unmount();

    window.history.pushState({}, '', '/recruiter/jobs/job-123/results');
    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Senior Product Designer' })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/recruiter/jobs',
      expect.objectContaining({ credentials: 'include' }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/recruiter/jobs/job-123/dashboard',
      expect.objectContaining({ credentials: 'include' }),
    );
  });

  it('creates a recruiter account through the auth route', async () => {
    window.history.pushState({}, '', '/auth');
    const fetchMock = vi.spyOn(window, 'fetch').mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ user: { id: 'recruiter-1' } }),
    } as Response);

    render(<App />);
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Recruiter' } });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'recruiter@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'secret123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/register',
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
    );
    expect(await screen.findByRole('status')).toHaveTextContent('Account created.');
  });

  it('creates a recruiter challenge through the coding editor route', async () => {
    window.history.pushState({}, '', '/recruiter/jobs/job-123/coding-challenges');
    const fetchMock = vi.spyOn(window, 'fetch').mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ id: 'challenge-1' }),
    } as Response);

    render(<App />);
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Sum numbers' } });
    fireEvent.change(screen.getByLabelText('Prompt'), { target: { value: 'Print the sum.' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save challenge' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/recruiter/jobs/job-123/coding-challenges',
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
    );
    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toMatchObject({
      title: 'Sum numbers',
      prompt: 'Print the sum.',
      allowed_languages: ['python', 'javascript'],
    });
    expect(await screen.findByRole('status')).toHaveTextContent('Challenge saved.');
  });

  it('loads and submits a candidate challenge through the public route', async () => {
    window.history.pushState({}, '', '/jobs/example-job/coding-challenges');
    const fetchMock = vi.spyOn(window, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [{
          id: 'challenge-1',
          title: 'Sum numbers',
          prompt: 'Print the sum.',
          allowed_languages: ['python'],
          public_test_cases: [{ input: '1 2', expected_output: '3' }],
        }],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ status: 'completed', score: 100 }),
      } as Response);

    render(<App />);
    expect(await screen.findByRole('heading', { name: 'Sum numbers' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Assessment token'), { target: { value: 'stage-token' } });
    fireEvent.change(screen.getByLabelText('Source code'), { target: { value: 'print(1 + 2)' } });
    fireEvent.click(screen.getByRole('button', { name: 'Submit challenge' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/public/jobs/example-job/coding-challenges',
      expect.any(Object),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/public/coding-challenges/challenge-1/submissions',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toMatchObject({
      assessment_token: 'stage-token',
      language: 'python',
      source: 'print(1 + 2)',
    });
    expect(await screen.findByRole('status')).toHaveTextContent(/completed/i);
  });
});
