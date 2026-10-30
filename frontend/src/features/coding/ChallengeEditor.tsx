import { useState, type FormEvent } from 'react';

type TestCase = {
  input: string;
  expected_output: string;
};

type ChallengeInput = {
  title: string;
  prompt: string;
  allowed_languages: string[];
  public_test_cases: TestCase[];
  private_test_cases: TestCase[];
};

type ChallengeEditorProps = {
  onSave?: (challenge: ChallengeInput) => void | Promise<void>;
};

function parseTestCases(value: string): TestCase[] {
  const parsed: unknown = JSON.parse(value);
  if (!Array.isArray(parsed) || parsed.some((item) =>
    !item ||
    typeof item !== 'object' ||
    typeof item.input !== 'string' ||
    typeof item.expected_output !== 'string'
  )) {
    throw new Error('Test cases must be a JSON array with input and expected_output strings.');
  }
  return parsed;
}

export default function ChallengeEditor({ onSave }: ChallengeEditorProps) {
  const [title, setTitle] = useState('');
  const [prompt, setPrompt] = useState('');
  const [languages, setLanguages] = useState('python, javascript');
  const [publicCases, setPublicCases] = useState('[{"input":"","expected_output":""}]');
  const [privateCases, setPrivateCases] = useState('[{"input":"","expected_output":""}]');
  const [error, setError] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (!title.trim() || !prompt.trim()) {
      setError('Title and prompt are required.');
      return;
    }

    try {
      const publicTestCases = parseTestCases(publicCases);
      const privateTestCases = parseTestCases(privateCases);
      if (privateTestCases.length === 0) {
        setError('At least one private test case is required.');
        return;
      }

      await onSave?.({
        title: title.trim(),
        prompt: prompt.trim(),
        allowed_languages: languages.split(',').map((item) => item.trim().toLowerCase()).filter(Boolean),
        public_test_cases: publicTestCases,
        private_test_cases: privateTestCases,
      });
    } catch (parseError) {
      setError(parseError instanceof Error ? parseError.message : 'Could not save the coding challenge.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="challenge-title">Title</label>
      <input id="challenge-title" value={title} onChange={(event) => setTitle(event.target.value)} />

      <label htmlFor="challenge-prompt">Prompt</label>
      <textarea id="challenge-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} />

      <label htmlFor="challenge-languages">Allowed languages</label>
      <input id="challenge-languages" value={languages} onChange={(event) => setLanguages(event.target.value)} />

      <label htmlFor="challenge-public-cases">Public test cases (JSON)</label>
      <textarea
        id="challenge-public-cases"
        value={publicCases}
        onChange={(event) => setPublicCases(event.target.value)}
      />

      <label htmlFor="challenge-private-cases">Private test cases (JSON)</label>
      <textarea
        id="challenge-private-cases"
        value={privateCases}
        onChange={(event) => setPrivateCases(event.target.value)}
      />

      {error ? <p role="alert">{error}</p> : null}
      <button type="submit">Save challenge</button>
    </form>
  );
}
