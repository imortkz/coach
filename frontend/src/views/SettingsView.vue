<template>
  <div class="max-w-lg mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-8 text-gray-900 dark:text-white">
      {{ t('settings.title') }}
    </h1>

    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        {{ t('settings.language_label') }}
      </label>

      <div class="flex gap-3">
        <button
          @click="selectLanguage('en')"
          :class="[
            'flex-1 py-2 px-4 rounded-lg border-2 font-medium transition-colors',
            settings.language === 'en'
              ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-300'
          ]"
        >
          {{ t('settings.language_en') }}
        </button>

        <button
          @click="selectLanguage('ru')"
          :class="[
            'flex-1 py-2 px-4 rounded-lg border-2 font-medium transition-colors',
            settings.language === 'ru'
              ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-300'
          ]"
        >
          {{ t('settings.language_ru') }}
        </button>
      </div>

      <p
        v-if="savedVisible"
        class="mt-3 text-sm text-green-600 dark:text-green-400 font-medium"
      >
        {{ t('settings.language_saved') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettingsStore, type Language } from '@/stores/settings'

const { t } = useI18n()
const settings = useSettingsStore()

const savedVisible = ref(false)
let savedTimer: ReturnType<typeof setTimeout> | null = null

async function selectLanguage(lang: Language) {
  if (settings.language === lang) return
  await settings.setLanguage(lang)
  savedVisible.value = true
  if (savedTimer) clearTimeout(savedTimer)
  savedTimer = setTimeout(() => {
    savedVisible.value = false
  }, 2000)
}
</script>
