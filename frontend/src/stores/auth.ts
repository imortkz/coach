import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export interface AuthUser {
  id: string
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  photo_url: string | null
}

const TOKEN_KEY = 'gymcoach_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<AuthUser | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem(TOKEN_KEY, t)
  }

  function clearToken() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      if (res.ok) {
        user.value = await res.json()
      } else {
        clearToken()
      }
    } catch {
      // Network error — keep token but user stays null
    }
  }

  async function devLogin() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/auth/dev-login', { method: 'POST' })
      if (!res.ok) throw new Error('Dev login failed')
      const data = await res.json()
      setToken(data.access_token)
      user.value = {
        id: data.user_id,
        telegram_id: 0,
        username: data.username ?? null,
        first_name: data.first_name,
        last_name: null,
        photo_url: null,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Login failed'
    } finally {
      loading.value = false
    }
  }

  async function telegramLogin(telegramData: Record<string, string | number>) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/auth/telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(telegramData),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: 'Login failed' }))
        throw new Error(detail.detail ?? 'Login failed')
      }
      const data = await res.json()
      setToken(data.access_token)
      user.value = {
        id: data.user_id,
        telegram_id: telegramData.id as number,
        username: (telegramData.username as string) ?? null,
        first_name: data.first_name,
        last_name: (telegramData.last_name as string) ?? null,
        photo_url: (telegramData.photo_url as string) ?? null,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Login failed'
    } finally {
      loading.value = false
    }
  }

  function logout() {
    clearToken()
  }

  return {
    token,
    user,
    loading,
    error,
    isAuthenticated,
    devLogin,
    telegramLogin,
    fetchMe,
    logout,
  }
})
