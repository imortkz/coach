/**
 * useApi — authenticated fetch wrapper.
 *
 * Automatically attaches the JWT Bearer token from the auth store to every
 * request. Redirects to /login on 401.
 */
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

export function useApi() {
  const auth = useAuthStore()
  const router = useRouter()

  async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = new Headers(options.headers)

    if (auth.token) {
      headers.set('Authorization', `Bearer ${auth.token}`)
    }
    if (!headers.has('Content-Type') && options.body) {
      headers.set('Content-Type', 'application/json')
    }

    const res = await fetch(url, { ...options, headers })

    if (res.status === 401) {
      auth.logout()
      router.push('/login')
    }

    return res
  }

  return { apiFetch }
}
