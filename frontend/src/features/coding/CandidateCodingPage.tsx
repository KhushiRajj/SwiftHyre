import { useState, type FormEvent } from 'react';

type Challenge = {
  id: string;
  title: string;
  prompt: string;
  allowed_languages: string[];
  public_test_cases?: Array<{ input: string; expected_output: string }>;
  private_test_cases?: Array<{ input: string; expected_output: string }>;
};

type CandidateSubmission = {
  challengeId: string;
  assessmentToken: string;
  language: string;
  source: string;
};

type CandidateCodingPageProps = {
  challenge: Challenge;
  assessmentToken: string;
  onSubmit?: (submission: CandidateSubmission) => void | Promise<void>;
};

export default function CandidateCodingPage({
  challenge,
  assessmentToken,
  onSubmit,
}: CandidateCodingPageProps) {
  const [language, setLanguage] = useState(challenge.allowed_languages[0] ?? '');
  const [token, setToken] = useState(assessmentToken);
  const [source, setSource] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (!token.trim()) {
      setError('An active coding assessment token is required.');
      return;
    }
    if (!language || !source.trim()) {
      setError('Choose a language and enter your code.');
      return;
    }

    try {
      await onSubmit?.({
        challengeId: challenge.id,
        assessmentToken: token.trim(),
        language,
        source,
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Could not submit the coding assessment.');
    }
  };

  return (
    <section>
      <h2>{challenge.title}</h2>
      <p>{challenge.prompt}</p>

      <h3>Public test cases</h3>
      <ul>
        {challenge.public_test_cases?.map((testCase, index) => (
          <li key={`${testCase.input}-${index}`}>
            Input: {testCase.input} | Expected output: {testCase.expected_output}
          </li>
        ))}
      </ul>

      <form onSubmit={handleSubmit}>
        <label htmlFor="coding-assessment-token">Assessment token</label>
        <input
          id="coding-assessment-token"
          value={token}
          onChange={(event) => setToken(event.target.value)}
          required
        />

        <label htmlFor="coding-language">Language</label>
        <select
          id="coding-language"
          value={language}
          onChange={(event) => setLanguage(event.target.value)}
          required
        >
          {challenge.allowed_languages.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>

        <label htmlFor="coding-source">Source code</label>
        <textarea
          id="coding-source"
          value={source}
          onChange={(event) => setSource(event.target.value)}
          required
        />

        {error ? <p role="alert">{error}</p> : null}
        <button type="submit">Submit challenge</button>
      </form>
    </section>
  );
}
