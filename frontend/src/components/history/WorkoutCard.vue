<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useExercisesStore } from '@/stores/exercises'
import { useDisplayName } from '@/composables/useDisplayName'
import type { Workout } from '@/types'

const props = defineProps<{
  workout: Workout
  expanded: boolean
  programName: string
}>()

const emit = defineEmits<{
  toggle: []
}>()

const { t } = useI18n()
const exercisesStore = useExercisesStore()
const { displayName } = useDisplayName()

// Compute display fields from workout data
const exerciseCount = computed(() => {
  const ids = new Set(props.workout.sets.map((s) => s.exercise_id))
  return ids.size
})

const totalSets = computed(() => {
  return props.workout.sets.filter((s) => !s.is_warmup).length
})

const durationDisplay = computed(() => {
  if (!props.workout.started_at || !props.workout.completed_at) return null
  const startRaw = props.workout.started_at
  const start = new Date(startRaw.endsWith('Z') ? startRaw : startRaw + 'Z')
  const endRaw = props.workout.completed_at!
  const end = new Date(endRaw.endsWith('Z') ? endRaw : endRaw + 'Z')
  const diffMs = end.getTime() - start.getTime()
  if (diffMs < 0) return null
  const totalMinutes = Math.round(diffMs / 60000)
  if (totalMinutes >= 60) {
    const hours = Math.floor(totalMinutes / 60)
    const mins = totalMinutes % 60
    return `${hours}${t('summary.hours_short')} ${mins}${t('summary.mins_short')}`
  }
  return `${totalMinutes}${t('summary.mins_short')}`
})

const formattedDate = computed(() => {
  const d = new Date(props.workout.completed_at || props.workout.started_at)
  return d.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
})

// Group sets by exercise for expanded view
interface ExerciseGroup {
  exerciseId: string
  displayName: string
  sets: { set_number: number; weight_kg: number | null; reps: number | null; is_warmup: boolean }[]
}

const exerciseGroups = computed<ExerciseGroup[]>(() => {
  const map = new Map<string, ExerciseGroup>()
  for (const s of props.workout.sets) {
    const exId = String(s.exercise_id)
    if (!map.has(exId)) {
      const exercise = exercisesStore.exercises.find((e) => e.id === exId)
      const name = exercise
        ? displayName(exercise)
        : (s.exercise?.name || `Exercise #${exId}`)
      map.set(exId, {
        exerciseId: exId,
        displayName: name,
        sets: [],
      })
    }
    map.get(exId)!.sets.push({
      set_number: s.set_number,
      weight_kg: s.weight_kg,
      reps: s.reps,
      is_warmup: s.is_warmup,
    })
  }
  return Array.from(map.values())
})

function formatWeight(weight_kg: number | null, reps: number | null): string {
  const w = weight_kg !== null ? `${weight_kg}${t('summary.kg')}` : t('history.bodyweight')
  const r = reps !== null ? `${reps} ${t('history.reps_short')}` : '-'
  return `${w} x ${r}`
}
</script>

<template>
  <div class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
    <!-- Card header (always visible) -->
    <button
      class="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors text-left"
      @click="emit('toggle')"
    >
      <div class="flex flex-col gap-0.5 min-w-0">
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-gray-900">{{ formattedDate }}</span>
          <span v-if="programName" class="text-xs text-gray-500 truncate">{{ programName }}</span>
        </div>
        <div class="flex items-center gap-3 text-xs text-gray-400">
          <span>{{ t('programs.exercise_count', exerciseCount) }}</span>
          <span>{{ t('workout.set_count', totalSets) }}</span>
          <span v-if="durationDisplay">{{ durationDisplay }}</span>
        </div>
      </div>
      <!-- Chevron -->
      <svg
        class="h-4 w-4 text-gray-400 transition-transform shrink-0"
        :class="{ 'rotate-180': expanded }"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Expanded detail section -->
    <Transition name="expand">
      <div v-if="expanded" class="border-t border-gray-100 px-4 py-3 space-y-3">
        <div v-for="group in exerciseGroups" :key="group.exerciseId">
          <RouterLink
            :to="`/exercises/${group.exerciseId}/history`"
            class="text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline"
          >
            {{ group.displayName }}
          </RouterLink>
          <ul class="mt-1 space-y-0.5">
            <li
              v-for="s in group.sets"
              :key="s.set_number"
              class="text-xs text-gray-600 flex items-center gap-1"
            >
              <span class="text-gray-400 w-12">{{ t('programs.set_n', { n: s.set_number }) }}</span>
              <span>{{ formatWeight(s.weight_kg, s.reps) }}</span>
              <span v-if="s.is_warmup" class="text-gray-400 text-[10px]">{{ t('history.warmup_short') }}</span>
            </li>
          </ul>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
