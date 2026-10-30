export type ApiError = {
  message?: string;
};

export type AuthUser = {
  id: string;
  name: string;
  email: string;
};

export async function registerRecruiter(payload: { name: string; email: string; password: string }): Promise<AuthUser> {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'same-origin',
  });

  const data = (await response.json()) as { user?: AuthUser; error?: string };
  if (!response.ok) {
    throw new Error(data.error ?? 'Registration failed');
  }

  return data.user as AuthUser;
}

export async function loginRecruiter(payload: { email: string; password: string }): Promise<AuthUser> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'same-origin',
  });

  const data = (await response.json()) as { user?: AuthUser; error?: string };
  if (!response.ok) {
    throw new Error(data.error ?? 'Login failed');
  }

  return data.user as AuthUser;
}

export async function logoutRecruiter(): Promise<void> {
  const response = await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'same-origin',
  });

  if (!response.ok) {
    throw new Error('Logout failed');
  }
}
