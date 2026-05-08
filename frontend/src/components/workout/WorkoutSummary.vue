<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Workout } from '@/types'

const { t } = useI18n()

const props = defineProps<{
  workout: Workout
  programName: string
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const durationText = computed(() => {
  if (!props.workout.started_at) return '--'
  const raw = props.workout.started_at
  const start = new Date(raw.endsWith('Z') ? raw : raw + 'Z').getTime()
  const now = Date.now()
  const totalMins = Math.floor((now - start) / 60000)
  if (totalMins < 60) return `${totalMins} ${t('summary.min_short')}`
  const hrs = Math.floor(totalMins / 60)
  const mins = totalMins % 60
  return `${hrs}${t('summary.hours_short')} ${mins}${t('summary.mins_short')}`
})

// Unique exercises with at least one logged set
const exerciseCount = computed(() => {
  const ids = new Set(props.workout.sets.map((s) => s.exercise_id))
  return ids.size
})

const totalSets = computed(() => props.workout.sets.length)

const totalVolume = computed(() => {
  let vol = 0
  for (const s of props.workout.sets) {
    if (s.weight_kg !== null && s.reps !== null) {
      vol += s.weight_kg * s.reps
    }
  }
  return vol
})

const volumeDisplay = computed(() => {
  if (totalVolume.value >= 1000) {
    return `${(totalVolume.value / 1000).toFixed(1)}${t('summary.kg_thousand')}`
  }
  return `${totalVolume.value.toLocaleString()} ${t('summary.kg')}`
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
    <div class="bg-white rounded-2xl shadow-xl max-w-sm w-full mx-4 overflow-hidden">
      <!-- Header -->
      <div class="px-6 pt-6 pb-4">
        <h2 class="text-xl font-bold text-gray-900">{{ t('summary.title') }}</h2>
        <p class="text-sm text-gray-500 mt-1">{{ programName }}</p>
      </div>

      <!-- Stats grid -->
      <div class="px-6 pb-6 grid grid-cols-2 gap-4">
        <div class="bg-gray-50 rounded-lg p-3">
          <p class="text-2xl font-bold text-gray-900">{{ durationText }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ t('summary.duration') }}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-3">
          <p class="text-2xl font-bold text-gray-900">{{ exerciseCount }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ t('summary.exercises_label', exerciseCount) }}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-3">
          <p class="text-2xl font-bold text-gray-900">{{ totalSets }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ t('summary.sets_label', totalSets) }}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-3">
          <p class="text-2xl font-bold text-gray-900">{{ volumeDisplay }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ t('summary.volume') }}</p>
        </div>
      </div>

      <!-- Actions -->
      <div class="px-6 pb-6 flex gap-3">
        <button
          class="flex-1 px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          @click="emit('cancel')"
        >
          {{ t('summary.keep_going') }}
        </button>
        <button
          class="flex-1 px-4 py-3 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
          @click="emit('confirm')"
        >
          {{ t('summary.finish') }}
        </button>
      </div>
    </div>
  </div>
</template>
