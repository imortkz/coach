import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiFetch } from '@/lib/apiFetch'
import i18n from '@/plugins/i18n'

export type Language = 'en' | 'ru'

function isLanguage(v: unknown): v is Language {
  return v === 'en' || v === 'ru'
}

export const useSettingsStore = defineStore('settings', () => {
  const language = ref<Language>('en')

  async function loadLanguage(): Promise<void> {
    try {
      const res = await apiFetch('/api/settings/language')
      if (res.status === 404) {
        // No preference saved yet — default to 'en'
        language.value = 'en'
        i18n.global.locale.value = 'en'
        return
      }
      if (!res.ok) {
        console.error(`[SettingsStore] loadLanguage error: ${res.status}`)
        return
      }
      const data = await res.json()
      const lang: Language = isLanguage(data.value) ? data.value : 'en'
      language.value = lang
      i18n.global.locale.value = lang
    } catch (err) {
      console.error('[SettingsStore] loadLanguage error:', err)
    }
  }

  async function setLanguage(lang: Language): Promise<void> {
    language.value = lang
    i18n.global.locale.value = lang
    try {
      await apiFetch('/api/settings/language', {
        method: 'PUT',
        body: JSON.stringify({ value: lang }),
      })
    } catch (err) {
      console.error('[SettingsStore] setLanguage error:', err)
    }
  }

  return { language, loadLanguage, setLanguage }
})
