<template>
  <div class="min-h-screen bg-gray-950 flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <!-- Logo / title -->
      <div class="text-center mb-10">
        <div class="text-5xl mb-3">🏋️</div>
        <h1 class="text-2xl font-bold text-white tracking-tight">GymCoach</h1>
        <p class="text-gray-400 text-sm mt-1">Your personal training companion</p>
      </div>

      <!-- Card -->
      <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
        <h2 class="text-white font-semibold text-lg mb-1">Sign in</h2>
        <p class="text-gray-400 text-sm mb-6">
          Connect with your Telegram account to get started.
        </p>

        <!-- Error message -->
        <div
          v-if="auth.error"
          class="mb-4 px-3 py-2 bg-red-900/40 border border-red-700/50 rounded-lg text-red-300 text-sm"
        >
          {{ auth.error }}
        </div>

        <!-- Telegram Login Widget container -->
        <div class="flex justify-center mb-4">
          <div id="telegram-login-widget" ref="widgetContainer"></div>
        </div>

        <!-- Dev mode login -->
        <div v-if="isDev" class="mt-4 pt-4 border-t border-gray-800">
          <p class="text-center text-xs text-gray-500 mb-3">Dev mode — no Telegram bot required</p>
          <button
            @click="handleDevLogin"
            :disabled="auth.loading"
            class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium py-2.5 rounded-xl transition-colors"
          >
            <span v-if="auth.loading">Signing in…</span>
            <span v-else>Continue as Dev User</span>
          </button>
        </div>
      </div>

      <p class="text-center text-gray-600 text-xs mt-6">
        Single-user app. Your data stays private.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const widgetContainer = ref<HTMLElement | null>(null)

// Dev mode = localhost or explicit env var
const isDev = import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === 'true'

async function handleDevLogin() {
  await auth.devLogin()
  if (!auth.error) {
    router.push('/')
  }
}

function loadTelegramWidget() {
  const botName = import.meta.env.VITE_TELEGRAM_BOT_NAME
  if (!botName || !widgetContainer.value) return

  // Remove existing script if any
  const existing = document.getElementById('telegram-login-script')
  existing?.remove()

  // Telegram widget calls window.onTelegramAuth with the login data
  ;(window as any).onTelegramAuth = async (tgData: Record<string, string | number>) => {
    await auth.telegramLogin(tgData)
    if (!auth.error) {
      router.push('/')
    }
  }

  const script = document.createElement('script')
  script.id = 'telegram-login-script'
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.setAttribute('data-telegram-login', botName)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '12')
  script.setAttribute('data-onauth', 'onTelegramAuth(user)')
  script.setAttribute('data-request-access', 'write')
  script.async = true

  widgetContainer.value.appendChild(script)
}

onMounted(async () => {
  // Already logged in?
  if (auth.isAuthenticated) {
    router.push('/')
    return
  }
  await nextTick()
  // Skip Telegram widget in dev mode — localhost isn't a registered bot domain
  if (!isDev) {
    loadTelegramWidget()
  }
})
</script>
