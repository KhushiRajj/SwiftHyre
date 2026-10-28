import { useState } from 'react';

export default function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('register');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (!email.trim() || !password.trim() || (mode === 'register' && !name.trim())) {
      setError('Please complete all fields.');
      return;
    }

    // Intentionally left for the backend implementation step.
  };

  return (
    <main>
      <h1>SwiftHyre</h1>
      <form onSubmit={handleSubmit}>
        {mode === 'register' ? (
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
        ) : null}
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error ? <p role="alert">{error}</p> : null}
        <button type="submit">{mode === 'register' ? 'Create account' : 'Sign in'}</button>
      </form>
      <button type="button" onClick={() => setMode(mode === 'register' ? 'login' : 'register')}>
        {mode === 'register' ? 'Already have an account?' : 'Need an account?'}
      </button>
    </main>
  );
}
