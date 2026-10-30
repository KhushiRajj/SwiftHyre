export async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    credentials: 'include',
    ...init,
  });
  const body: unknown = await response.json();

  if (!response.ok) {
    const message = typeof body === 'object'
      && body !== null
      && 'error' in body
      && typeof body.error === 'string'
      ? body.error
      : undefined;
    throw new Error(message || 'The request could not be completed.');
  }

  return body as T;
}
