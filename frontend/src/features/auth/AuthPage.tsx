import { useState } from 'react';

type AuthCredentials = {
  mode: 'login' | 'register';
  name: string;
  email: string;
  password: string;
};

type AuthPageProps = {
  onSubmit?: (credentials: AuthCredentials) => void | Promise<void>;
};

export default function AuthPage({ onSubmit }: AuthPageProps = {}) {
  const [mode, setMode] = useState<'login' | 'register'>('register');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    if (!email.trim() || !password.trim() || (mode === 'register' && !name.trim())) {
      setError('Please complete all fields.');
      return;
    }

    try {
      await onSubmit?.({ mode, name: name.trim(), email: email.trim(), password });
      setSuccess(mode === 'register' ? 'Account created.' : 'Signed in.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Authentication failed.');
    }
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
      {success ? <p role="status">{success}</p> : null}
      <button type="button" onClick={() => setMode(mode === 'register' ? 'login' : 'register')}>
        {mode === 'register' ? 'Already have an account?' : 'Need an account?'}
      </button>
    </main>
  );
}
