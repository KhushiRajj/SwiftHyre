import { fireEvent, render, screen } from '@testing-library/react';
import CandidateCodingPage from './CandidateCodingPage';
import ChallengeEditor from './ChallengeEditor';

describe('Coding challenge UI', () => {
  it('lets recruiters author a challenge with the required fields', () => {
    render(<ChallengeEditor />);

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/prompt/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/allowed languages/i)).toBeInTheDocument();
    expect(screen.getByText(/private test cases/i)).toBeInTheDocument();
  });

  it('submits recruiter-authored public and private cases', () => {
    const onSave = vi.fn();
    render(<ChallengeEditor onSave={onSave} />);

    fireEvent.change(screen.getByLabelText(/title/i), { target: { value: 'Echo' } });
    fireEvent.change(screen.getByLabelText(/prompt/i), { target: { value: 'Echo input.' } });
    fireEvent.change(screen.getByLabelText(/public test cases/i), {
      target: { value: '[{"input":"hi","expected_output":"hi"}]' },
    });
    fireEvent.change(screen.getByLabelText(/private test cases/i), {
      target: { value: '[{"input":"hidden","expected_output":"hidden"}]' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save challenge/i }));

    expect(onSave).toHaveBeenCalledWith({
      title: 'Echo',
      prompt: 'Echo input.',
      allowed_languages: ['python', 'javascript'],
      public_test_cases: [{ input: 'hi', expected_output: 'hi' }],
      private_test_cases: [{ input: 'hidden', expected_output: 'hidden' }],
    });
  });

  it('shows public prompt data without leaking hidden tests to candidates', () => {
    render(
      <CandidateCodingPage
        assessmentToken="stage-token"
        challenge={{
          id: 'challenge-1',
          title: 'String parser',
          prompt: 'Return the total count of digits in the input string.',
          allowed_languages: ['python'],
          public_test_cases: [{ input: 'abc123', expected_output: '3' }],
          private_test_cases: [{ input: 'a1b2c3', expected_output: 'hidden-answer' }],
        }}
      />
    );

    expect(screen.getByText(/return the total count of digits/i)).toBeInTheDocument();
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.queryByText(/a1b2c3/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/hidden-answer/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit challenge/i })).toBeInTheDocument();
  });

  it('submits the selected language, source, and stage token', () => {
    const onSubmit = vi.fn();
    render(
      <CandidateCodingPage
        assessmentToken="stage-token"
        challenge={{
          id: 'challenge-2',
          title: 'Echo',
          prompt: 'Echo input.',
          allowed_languages: ['python', 'javascript'],
        }}
        onSubmit={onSubmit}
      />
    );

    fireEvent.change(screen.getByLabelText(/source code/i), {
      target: { value: 'print(input())' },
    });
    fireEvent.change(screen.getByLabelText(/language/i), {
      target: { value: 'javascript' },
    });
    fireEvent.click(screen.getByRole('button', { name: /submit challenge/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      challengeId: 'challenge-2',
      assessmentToken: 'stage-token',
      language: 'javascript',
      source: 'print(input())',
    });
  });
});
