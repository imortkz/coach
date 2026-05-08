/**
 * apiFetch — thin wrapper around fetch that injects the JWT Bearer token.
 *
 * Reads the token directly from localStorage so it can be used outside
 * of Vue component context (i.e. inside Pinia stores).
 */

const TOKEN_KEY = 'gymcoach_token'

export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = localStorage.getItem(TOKEN_KEY)
  const headers = new Headers(options.headers)

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }

  return fetch(url, { ...options, headers })
}
