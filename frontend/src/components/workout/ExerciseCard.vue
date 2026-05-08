<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Exercise, WorkoutSet, ProgramSet, PreFillSet, SuggestionInfo } from '@/types'
import { useI18n } from 'vue-i18n'
import { useWorkoutsStore } from '@/stores/workouts'
import { useDisplayName } from '@/composables/useDisplayName'
import SetRow from './SetRow.vue'

const { t } = useI18n()
const { displayName } = useDisplayName()

const props = withDefaults(defineProps<{
  exercise: Exercise
  loggedSets: WorkoutSet[]
  templateSets: ProgramSet[]
  preFillSets: PreFillSet[]
  extraSetNumbers?: number[]
  skippedTemplateSets?: Set<string>
}>(), {
  extraSetNumbers: () => [],
  skippedTemplateSets: () => new Set<string>(),
})

const emit = defineEmits<{
  addSet: [exerciseId: string]
  setLogged: []
  deleteSet: [setId: number]
  removeExtra: [exerciseId: string, setNumber: number]
  removeExercise: [exerciseId: string]
  removeTemplate: [payload: { exerciseId: string; setNumber: number }]
}>()

const workoutsStore = useWorkoutsStore()
const showRemoveConfirm = ref(false)
const showMenu = ref(false)

// Build the list of set rows: template sets + any extra logged sets beyond template count
const setRows = computed(() => {
  const rows: Array<{
    setNumber: number
    loggedSet: WorkoutSet | null
    templateSet: ProgramSet | null
    preFillSet: PreFillSet | null
    isWarmup: boolean
    isExtra: boolean
  }> = []

  // Template-defined sets (excluding skipped unlogged template sets)
  for (const ts of props.templateSets) {
    const logged = props.loggedSets.find(
      (s) => s.set_number === ts.set_number && s.exercise_id === props.exercise.id
    )
    // Skip unlogged template sets that have been dismissed by the user
    if (!logged && props.skippedTemplateSets.has(`${props.exercise.id}:${ts.set_number}`)) {
      continue
    }
    const pf = props.preFillSets.find((p) => p.set_number === ts.set_number)
    rows.push({
      setNumber: ts.set_number,
      loggedSet: logged ?? null,
      templateSet: ts,
      preFillSet: pf ?? null,
      isWarmup: ts.is_warmup,
      isExtra: false,
    })
  }

  // Extra logged sets beyond template
  const templateNumbers = new Set(props.templateSets.map((ts) => ts.set_number))
  const extras = props.loggedSets
    .filter((s) => !templateNumbers.has(s.set_number))
    .sort((a, b) => a.set_number - b.set_number)

  for (const extra of extras) {
    rows.push({
      setNumber: extra.set_number,
      loggedSet: extra,
      templateSet: null,
      preFillSet: null,
      isWarmup: extra.is_warmup,
      isExtra: true,
    })
  }

  // Pending extra sets (added by user, not yet logged)
  const existingNumbers = new Set(rows.map((r) => r.setNumber))
  for (const num of props.extraSetNumbers) {
    if (!existingNumbers.has(num)) {
      rows.push({
        setNumber: num,
        loggedSet: null,
        templateSet: null,
        preFillSet: null,
        isWarmup: false,
        isExtra: true,
      })
    }
  }

  return rows
})

// Suggestion for this exercise from the store
const exerciseSuggestion = computed<SuggestionInfo | null>(() => {
  return workoutsStore.suggestions[props.exercise.id] ?? null
})

// Determine which set number should show the suggestion indicator (first uncompleted non-warmup set)
const suggestionSetNumber = computed<number | null>(() => {
  if (!exerciseSuggestion.value) return null
  for (const row of setRows.value) {
    if (!row.isWarmup && !row.loggedSet) {
      return row.setNumber
    }
  }
  return null
})

async function handleComplete(payload: {
  exercise_id: string
  set_number: number
  weight_kg: number | null
  reps: number | null
  is_warmup: boolean
}) {
  try {
    await workoutsStore.logSet(payload)
    emit('setLogged')
  } catch {
    // error is set in store
  }
}

async function handleUpdate(payload: { setId: number; weight_kg: number | null; reps: number | null }) {
  try {
    await workoutsStore.updateSet(payload.setId, {
      weight_kg: payload.weight_kg,
      reps: payload.reps,
    })
  } catch {
    // error is set in store
  }
}

function handleDeleteSet(setId: number) {
  emit('deleteSet', setId)
}

function handleRemoveExtra(setNumber: number) {
  emit('removeExtra', props.exercise.id, setNumber)
}

function handleRemoveTemplate(payload: { exerciseId: string; setNumber: number }) {
  emit('removeTemplate', payload)
}

function handleAddSet() {
  emit('addSet', props.exercise.id)
}

function handleRemoveClick() {
  showMenu.value = false
  showRemoveConfirm.value = true
}

function confirmRemove() {
  showRemoveConfirm.value = false
  emit('removeExercise', props.exercise.id)
}

function cancelRemove() {
  showRemoveConfirm.value = false
}
</script>

<template>
  <div class="border border-gray-200 rounded-lg overflow-hidden">
    <!-- Exercise header -->
    <div class="px-4 py-3 bg-gray-50/80 border-b border-gray-100 flex items-center justify-between">
      <div>
        <h3 class="font-semibold text-gray-900">{{ displayName(exercise) }}</h3>
        <p class="text-xs text-gray-500 mt-0.5">{{ t('muscle_groups.' + exercise.muscle_group) }} &middot; {{ exercise.equipment }}</p>
      </div>
      <!-- Menu button -->
      <div class="relative">
        <button
          class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          @click="showMenu = !showMenu"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <circle cx="10" cy="4" r="1.5" />
            <circle cx="10" cy="10" r="1.5" />
            <circle cx="10" cy="16" r="1.5" />
          </svg>
        </button>
        <!-- Dropdown menu -->
        <div
          v-if="showMenu"
          class="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-20 min-w-[160px]"
        >
          <button
            class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
            @click="handleRemoveClick"
          >
            Remove Exercise
          </button>
        </div>
        <!-- Click-away for menu -->
        <div
          v-if="showMenu"
          class="fixed inset-0 z-10"
          @click="showMenu = false"
        />
      </div>
    </div>

    <!-- Remove confirmation -->
    <div
      v-if="showRemoveConfirm"
      class="px-4 py-3 bg-red-50 border-b border-red-100 flex items-center justify-between gap-2"
    >
      <p class="text-sm text-red-800">Remove exercise and all its sets?</p>
      <div class="flex items-center gap-2 flex-shrink-0">
        <button
          class="px-3 py-1.5 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
          @click="confirmRemove"
        >
          Yes, Remove
        </button>
        <button
          class="px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
          @click="cancelRemove"
        >
          No
        </button>
      </div>
    </div>

    <!-- Set rows -->
    <div class="divide-y divide-gray-100">
      <!-- Column header -->
      <div class="flex items-center gap-2 px-3 py-1.5 text-xs text-gray-400 font-medium">
        <div class="w-8 text-center">Set</div>
        <div class="w-16 text-center">Weight</div>
        <div class="w-4"></div>
        <div class="w-1"></div>
        <div class="w-14 text-center">Reps</div>
        <div class="ml-auto w-8"></div>
      </div>

      <SetRow
        v-for="row in setRows"
        :key="`${exercise.id}-${row.setNumber}`"
        :set-number="row.setNumber"
        :logged-set="row.loggedSet"
        :template-set="row.templateSet"
        :pre-fill-set="row.preFillSet"
        :is-warmup="row.isWarmup"
        :is-extra="row.isExtra"
        :exercise-id="exercise.id"
        :suggestion="exerciseSuggestion"
        :show-suggestion="row.setNumber === suggestionSetNumber"
        @complete="handleComplete"
        @update="handleUpdate"
        @delete="handleDeleteSet"
        @remove-extra="handleRemoveExtra"
        @remove-template="handleRemoveTemplate"
      />
    </div>

    <!-- Add Set button -->
    <button
      class="w-full px-4 py-2.5 text-sm text-blue-600 hover:bg-blue-50/50 transition-colors border-t border-gray-100 font-medium"
      @click="handleAddSet"
    >
      + Add Set
    </button>
  </div>
</template>
