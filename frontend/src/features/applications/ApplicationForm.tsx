import { ChangeEvent, FormEvent, useState } from 'react';

export default function ApplicationForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [cv, setCv] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setCv(event.target.files?.[0] ?? null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitted(false);
    setError('');

    if (!name.trim() || !email.trim() || !cv) {
      setError('Please complete all fields.');
      return;
    }

    const isPdf = cv.type === 'application/pdf' || cv.name.toLowerCase().endsWith('.pdf');
    if (!isPdf || cv.size > 10 * 1024 * 1024) {
      setError('Please upload a PDF file under 10 MiB.');
      return;
    }

    setIsSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 200));
    setIsSubmitting(false);
    setSubmitted(true);
    setName('');
    setEmail('');
    setCv(null);
  };

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="full-name">Full name</label>
      <input id="full-name" value={name} onChange={(event) => setName(event.target.value)} />

      <label htmlFor="email-address">Email address</label>
      <input id="email-address" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />

      <label htmlFor="cv-upload">CV upload</label>
      <input id="cv-upload" type="file" accept=".pdf,application/pdf" onChange={handleFileChange} />

      {error ? <p role="alert">{error}</p> : null}
      {submitted ? <p>Application submitted.</p> : null}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit application'}
      </button>
    </form>
  );
}
