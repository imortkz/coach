<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useExercisesStore } from '@/stores/exercises'
import { useDisplayName } from '@/composables/useDisplayName'
import ExerciseChart from '@/components/history/ExerciseChart.vue'
import SessionTable from '@/components/history/SessionTable.vue'
import { apiFetch } from '@/lib/apiFetch'
import type { Exercise, ExerciseHistoryResponse, SuggestionInfo } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { displayName } = useDisplayName()
const exercisesStore = useExercisesStore()

const exerciseId = route.params.id as string
const exercise = ref<Exercise | null>(null)
const sessions = ref<ExerciseHistoryResponse['sessions']>([])
const suggestion = ref<SuggestionInfo | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function loadData() {
  loading.value = true
  error.value = null
  try {
    // Load exercise details
    if (exercisesStore.exercises.length === 0) {
      await exercisesStore.fetchExercises()
    }
    exercise.value = exercisesStore.exercises.find((e) => e.id === exerciseId) ?? null

    // Load history
    const params = new URLSearchParams()
    params.set('limit', '20')
    const programId = route.query.program_id
    if (programId) {
      params.set('program_id', String(programId))
    }

    const res = await apiFetch(`/api/exercises/${exerciseId}/history?${params}`)
    if (!res.ok) throw new Error(`Failed to load history: ${res.statusText}`)
    const data: ExerciseHistoryResponse = await res.json()
    sessions.value = data.sessions
    suggestion.value = data.suggestion
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load exercise history'
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.back()
}

onMounted(loadData)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-4">
      <button
        class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
        @click="goBack"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div>
        <h1 class="text-xl font-bold text-gray-900">
          {{ exercise ? displayName(exercise) : t('exercises.title') }}
        </h1>
        <p v-if="exercise" class="text-xs text-gray-500">
          {{ t('muscle_groups.' + exercise.muscle_group) }} &middot; {{ exercise.equipment }}
        </p>
      </div>
    </div>
    <!-- GIF display -->
    <img
      v-if="exercise?.gif_url"
      :src="exercise.gif_url"
      :alt="exercise ? displayName(exercise) : ''"
      class="w-full max-w-md mx-auto rounded-lg mt-4 block"
      @error="($event.target as HTMLImageElement).style.display = 'none'"
    />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <span class="ml-3 text-sm text-gray-500">{{ t('history.loading') }}</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-sm text-red-600">{{ error }}</p>
      <button
        class="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium"
        @click="loadData"
      >
        {{ t('exercises.try_again') }}
      </button>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Progression suggestion banner -->
      <div
        v-if="suggestion && suggestion.type === 'weight'"
        class="mb-4 px-4 py-3 rounded-lg bg-emerald-50 border border-emerald-200"
      >
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
          <p class="text-sm font-medium text-emerald-800">
            Next session: try {{ suggestion.suggested_weight_kg }}kg
            <span v-if="suggestion.increment" class="text-emerald-600">(+{{ suggestion.increment }})</span>
          </p>
        </div>
      </div>

      <div
        v-else-if="suggestion && suggestion.type === 'reps'"
        class="mb-4 px-4 py-3 rounded-lg bg-emerald-50 border border-emerald-200"
      >
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
          <p class="text-sm font-medium text-emerald-800">
            Next session: try {{ suggestion.suggested_reps }} reps (+1)
          </p>
        </div>
      </div>

      <div
        v-else-if="suggestion && suggestion.type === 'keep'"
        class="mb-4 px-4 py-3 rounded-lg bg-amber-50 border border-amber-200"
      >
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <p class="text-sm font-medium text-amber-800">
            Keep at {{ suggestion.suggested_weight_kg }}kg -- missed reps last time
          </p>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="sessions.length === 0" class="text-center py-12">
        <p class="text-gray-500 text-sm">No workout history for this exercise yet.</p>
        <p class="text-gray-400 text-xs mt-1">Complete a workout that includes this exercise to see data here.</p>
      </div>

      <template v-else>
        <!-- Chart (needs at least 2 data points) -->
        <div class="mb-4">
          <div v-if="sessions.length > 1">
            <ExerciseChart :sessions="sessions" />
          </div>
          <div v-else class="bg-white rounded-lg border border-gray-200 px-4 py-8 text-center">
            <p class="text-sm text-gray-400">Not enough data for chart (need at least 2 sessions)</p>
          </div>
        </div>

        <!-- Session table -->
        <div class="mb-4">
          <h2 class="text-sm font-semibold text-gray-700 mb-2">Recent Sessions</h2>
          <SessionTable :sessions="sessions" />
        </div>
      </template>
    </template>
  </div>
</template>
