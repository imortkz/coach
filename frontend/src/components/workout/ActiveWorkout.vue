<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWorkoutsStore } from '@/stores/workouts'
import { useProgramsStore } from '@/stores/programs'
import { useRestTimer } from '@/composables/useRestTimer'
import { apiFetch } from '@/lib/apiFetch'
import type { Program, ProgramExercise, WorkoutSet, PreFillSet } from '@/types'
import ExerciseCard from './ExerciseCard.vue'
import RestTimer from './RestTimer.vue'
import UndoToast from './UndoToast.vue'
import WorkoutSummary from './WorkoutSummary.vue'
import ProgramPicker from './ProgramPicker.vue'

const { t } = useI18n()
const workoutsStore = useWorkoutsStore()
const programsStore = useProgramsStore()

const program = ref<Program | null>(null)
const finishing = ref(false)
const showSummary = ref(false)
const restTimerSeconds = ref(120)
const restTimer = useRestTimer(restTimerSeconds.value)

// Reactive clock for elapsed time display
const now = ref(Date.now())
let tickInterval: ReturnType<typeof setInterval> | null = null

// Undo toast state
const undoToast = ref<{ message: string; undo: () => void } | null>(null)
let undoTimeoutId: ReturnType<typeof setTimeout> | null = null

// Track pending deletes for cleanup on navigation
const pendingDeletes = ref<Array<() => void>>([])

// Provide undo toast to children
provide('showUndoToast', showUndoToastFn)
provide('pendingDeletes', pendingDeletes)

function showUndoToastFn(message: string, undoFn: () => void, deleteFn: () => void, timeoutMs: number = 7000) {
  // Clear any existing undo toast
  if (undoTimeoutId !== null) {
    clearTimeout(undoTimeoutId)
    // Execute the previous pending delete immediately
    const prevDelete = pendingDeletes.value.shift()
    if (prevDelete) prevDelete()
  }

  undoToast.value = {
    message,
    undo: () => {
      if (undoTimeoutId !== null) clearTimeout(undoTimeoutId)
      undoTimeoutId = null
      undoFn()
      undoToast.value = null
      pendingDeletes.value = pendingDeletes.value.filter((d) => d !== deleteFn)
    },
  }

  pendingDeletes.value.push(deleteFn)
  undoTimeoutId = setTimeout(() => {
    deleteFn()
    undoToast.value = null
    undoTimeoutId = null
    pendingDeletes.value = pendingDeletes.value.filter((d) => d !== deleteFn)
  }, timeoutMs)
}

onMounted(async () => {
  // Update "now" every minute so durationText recomputes
  tickInterval = setInterval(() => {
    now.value = Date.now()
  }, 60000)

  // Fetch rest timer setting
  restTimerSeconds.value = await workoutsStore.fetchRestTimerSetting()

  if (workoutsStore.activeWorkout?.program_id) {
    try {
      program.value = await programsStore.fetchProgram(workoutsStore.activeWorkout.program_id)
    } catch {
      // program fetch failed, we can still show sets without template info
    }
  }
})

onUnmounted(() => {
  if (tickInterval !== null) {
    clearInterval(tickInterval)
    tickInterval = null
  }
})

const timerDisabled = computed(() => program.value?.rest_timer_disabled ?? false)

const removedExerciseIds = ref(new Set<string>())
const skippedTemplateSets = ref(new Set<string>())

const orderedExercises = computed<ProgramExercise[]>(() => {
  if (!program.value) return []
  return [...program.value.exercises]
    .filter((pe) => !removedExerciseIds.value.has(pe.exercise_id))
    .sort((a, b) => a.order - b.order)
})

// Group logged sets by exercise_id
const setsByExercise = computed<Record<string, WorkoutSet[]>>(() => {
  const grouped: Record<string, WorkoutSet[]> = {}
  if (!workoutsStore.activeWorkout) return grouped
  for (const s of workoutsStore.activeWorkout.sets) {
    if (!grouped[s.exercise_id]) grouped[s.exercise_id] = []
    grouped[s.exercise_id].push(s)
  }
  return grouped
})

function getPreFillSets(exerciseId: string): PreFillSet[] {
  return workoutsStore.preFill[exerciseId] ?? []
}

function getLoggedSets(exerciseId: string): WorkoutSet[] {
  return setsByExercise.value[exerciseId] ?? []
}

function getExtraSetNumbers(exerciseId: string): number[] {
  return extraSets.value
    .filter((e) => e.exerciseId === exerciseId)
    .map((e) => e.setNumber)
}

// Extra sets added by user (not yet logged, beyond template)
const extraSets = ref<Array<{
  exerciseId: string
  setNumber: number
}>>([])

function handleAddSet(exerciseId: string) {
  const loggedNums = getLoggedSets(exerciseId).map((s) => s.set_number)
  const pe = orderedExercises.value.find((e) => e.exercise_id === exerciseId)
  const templateNums = pe ? pe.sets.map((s) => s.set_number) : []
  const existingExtraNums = extraSets.value
    .filter((e) => e.exerciseId === exerciseId)
    .map((e) => e.setNumber)
  const allNums = [...loggedNums, ...templateNums, ...existingExtraNums]
  const nextNum = allNums.length > 0 ? Math.max(...allNums) + 1 : 1
  extraSets.value.push({ exerciseId, setNumber: nextNum })
}

function handleSetLogged() {
  // Start rest timer after a set is logged (unless disabled for this program)
  if (!timerDisabled.value) {
    restTimer.start(restTimerSeconds.value)
  }
}

function handleDeleteSet(setId: number) {
  if (!workoutsStore.activeWorkout) return
  // Optimistic removal
  const removedSet = workoutsStore.activeWorkout.sets.find((s) => s.id === setId)
  if (!removedSet) return
  workoutsStore.activeWorkout.sets = workoutsStore.activeWorkout.sets.filter((s) => s.id !== setId)

  showUndoToastFn(
    t('workout.toast_set_deleted'),
    () => {
      // Undo: restore the set locally
      if (workoutsStore.activeWorkout) {
        workoutsStore.activeWorkout.sets.push(removedSet)
      }
    },
    () => {
      // Permanently delete on server
      workoutsStore.deleteSet(setId).catch(() => {
        // If server delete fails, the set is already removed locally.
        // Could restore, but set was already removed from UI.
      })
    },
  )
}

function handleRemoveExtra(exerciseId: string, setNumber: number) {
  extraSets.value = extraSets.value.filter(
    (e) => !(e.exerciseId === exerciseId && e.setNumber === setNumber)
  )
}

function handleRemoveTemplate({ exerciseId, setNumber }: { exerciseId: string; setNumber: number }) {
  const key = `${exerciseId}:${setNumber}`
  skippedTemplateSets.value.add(key)
  // Trigger reactivity: replace the set with a new instance
  skippedTemplateSets.value = new Set(skippedTemplateSets.value)

  showUndoToastFn(
    t('workout.toast_set_skipped'),
    () => {
      // Undo: restore the template set row
      skippedTemplateSets.value.delete(key)
      skippedTemplateSets.value = new Set(skippedTemplateSets.value)
    },
    () => {
      // No backend call — template sets are never logged
    },
  )
}

function handleRemoveExercise(exerciseId: string) {
  if (!workoutsStore.activeWorkout) return
  removedExerciseIds.value.add(exerciseId)
  workoutsStore.deleteExerciseSets(exerciseId)
}

// Discard workout state
const discarding = ref(false)
let savedWorkout: typeof workoutsStore.activeWorkout = null
let savedPreFill: typeof workoutsStore.preFill = {}

function handleDiscard() {
  if (!workoutsStore.activeWorkout) return
  const workoutId = workoutsStore.activeWorkout.id
  savedWorkout = JSON.parse(JSON.stringify(workoutsStore.activeWorkout))
  savedPreFill = JSON.parse(JSON.stringify(workoutsStore.preFill))
  discarding.value = true

  showUndoToastFn(
    t('workout.toast_workout_discarded'),
    () => {
      // Undo: restore workout
      discarding.value = false
    },
    () => {
      // Permanently delete on server, then clear store
      apiFetch(`/api/workouts/${workoutId}`, { method: 'DELETE' }).catch(() => {})
      workoutsStore.activeWorkout = null
      workoutsStore.preFill = {}
      discarding.value = false
    },
  )
}

defineExpose({ flushPendingDeletes, discarding })

function handleFinish() {
  showSummary.value = true
}

async function handleConfirmFinish() {
  finishing.value = true
  try {
    await workoutsStore.completeWorkout()
    workoutsStore.activeWorkout = null
    workoutsStore.preFill = {}
    showSummary.value = false
  } catch {
    // error set in store
  } finally {
    finishing.value = false
  }
}

function handleCancelFinish() {
  showSummary.value = false
}

// Flush pending deletes on unmount
function flushPendingDeletes() {
  if (undoTimeoutId !== null) {
    clearTimeout(undoTimeoutId)
    undoTimeoutId = null
  }
  for (const deleteFn of pendingDeletes.value) {
    deleteFn()
  }
  pendingDeletes.value = []
  undoToast.value = null
}

// Compute total logged sets count
const totalLoggedSets = computed(() => {
  return workoutsStore.activeWorkout?.sets.length ?? 0
})

// Duration since workout started
const durationText = computed(() => {
  if (!workoutsStore.activeWorkout?.started_at) return ''
  const raw = workoutsStore.activeWorkout.started_at
  const start = new Date(raw.endsWith('Z') ? raw : raw + 'Z').getTime()
  const nowMs = now.value
  const mins = Math.floor((nowMs - start) / 60000)
  if (mins < 60) return `${mins}m`
  const hrs = Math.floor(mins / 60)
  const rem = mins % 60
  return `${hrs}h ${rem}m`
})
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Workout Summary modal -->
    <WorkoutSummary
      v-if="showSummary && workoutsStore.activeWorkout"
      :workout="workoutsStore.activeWorkout"
      :program-name="program?.name ?? t('workout.default_program_name')"
      @confirm="handleConfirmFinish"
      @cancel="handleCancelFinish"
    />

    <template v-if="!discarding">
      <!-- Sticky header -->
      <div class="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-gray-100 -mx-4 px-4 py-3 mb-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-lg font-bold text-gray-900">
              {{ program?.name ?? t('workout.default_program_name') }}
            </h1>
            <p class="text-xs text-gray-500">
              {{ t('workout.sets_logged', totalLoggedSets) }}
              <span v-if="durationText" class="ml-1">&middot; {{ durationText }}</span>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium"
              @click="handleDiscard"
            >
              {{ t('workout.discard') }}
            </button>
            <button
              class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              :disabled="finishing"
              @click="handleFinish"
            >
              {{ finishing ? t('workout.finishing') : t('workout.finish') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Exercise cards -->
      <div v-if="orderedExercises.length > 0" class="space-y-4 pb-32">
        <ExerciseCard
          v-for="pe in orderedExercises"
          :key="pe.exercise_id"
          :exercise="pe.exercise!"
          :logged-sets="getLoggedSets(pe.exercise_id)"
          :template-sets="pe.sets"
          :pre-fill-sets="getPreFillSets(pe.exercise_id)"
          :extra-set-numbers="getExtraSetNumbers(pe.exercise_id)"
          :skipped-template-sets="skippedTemplateSets"
          @add-set="handleAddSet"
          @set-logged="handleSetLogged"
          @delete-set="handleDeleteSet"
          @remove-extra="handleRemoveExtra"
          @remove-exercise="handleRemoveExercise"
          @remove-template="handleRemoveTemplate"
        />
      </div>

      <div v-else class="text-center py-12 text-gray-500">
        <p>{{ t('workout.loading_exercises') }}</p>
      </div>

      <!-- Rest Timer -->
      <RestTimer
        :remaining="restTimer.remaining.value"
        :is-running="restTimer.isRunning.value"
        :total-seconds="restTimerSeconds"
        @skip="restTimer.skip()"
      />
    </template>

    <!-- Show programs list (non-interactive) during discard countdown -->
    <ProgramPicker v-else class="pointer-events-none opacity-75" />

    <!-- Undo Toast -->
    <UndoToast
      :message="undoToast?.message ?? ''"
      :visible="undoToast !== null"
      @undo="undoToast?.undo()"
    />
  </div>
</template>
