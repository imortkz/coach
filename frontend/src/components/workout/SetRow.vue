<script setup lang="ts">
import { ref, computed, watch, useTemplateRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSwipeLeft } from '@/composables/useSwipeLeft'
import type { WorkoutSet, PreFillSet, ProgramSet, SuggestionInfo } from '@/types'

const { t } = useI18n()

const props = defineProps<{
  setNumber: number
  loggedSet: WorkoutSet | null
  preFillSet: PreFillSet | null
  templateSet: ProgramSet | null
  isWarmup: boolean
  exerciseId: string
  isExtra?: boolean
  suggestion?: SuggestionInfo | null
  showSuggestion?: boolean
}>()

const emit = defineEmits<{
  complete: [payload: {
    exercise_id: string
    set_number: number
    weight_kg: number | null
    reps: number | null
    is_warmup: boolean
  }]
  update: [payload: { setId: string; weight_kg: number | null; reps: number | null }]
  delete: [setId: string]
  removeExtra: [setNumber: number]
  removeTemplate: [payload: { exerciseId: string; setNumber: number }]
}>()

// Determine initial values: logged > suggestion (if shown) > prefill > template > empty
function getInitialWeight(): number | null {
  if (props.loggedSet) return props.loggedSet.weight_kg
  if (props.showSuggestion && props.suggestion?.type === 'weight' && props.suggestion.suggested_weight_kg !== null) {
    return props.suggestion.suggested_weight_kg
  }
  if (props.preFillSet) return props.preFillSet.weight_kg
  if (props.templateSet) return props.templateSet.target_weight_kg
  return null
}

function getInitialReps(): number | null {
  if (props.loggedSet) return props.loggedSet.reps
  if (props.showSuggestion && props.suggestion?.type === 'reps' && props.suggestion.suggested_reps !== null) {
    return props.suggestion.suggested_reps
  }
  if (props.preFillSet) return props.preFillSet.reps
  if (props.templateSet) return props.templateSet.target_reps
  return null
}

// Whether to show suggestion indicator on this row
const hasSuggestionIndicator = computed(() => {
  return !isLogged.value && props.showSuggestion && props.suggestion && props.suggestion.type !== 'keep'
})

const suggestionType = computed(() => props.suggestion?.type ?? null)

// "Last time" reference: what this set was in the previous session (#1).
const lastTimeText = computed<string | null>(() => {
  const pf = props.preFillSet
  if (!pf || (pf.weight_kg == null && pf.reps == null)) return null
  const w = pf.weight_kg != null ? `${pf.weight_kg}` : '—'
  const r = pf.reps != null ? `${pf.reps}` : '—'
  return `${w} × ${r}`
})

// Explicit progression recommendation (#2): show the target as words, not just
// a silent prefill. Only on the suggestion row, and only when it's a real bump.
const recommendationText = computed<string | null>(() => {
  if (!hasSuggestionIndicator.value) return null
  const s = props.suggestion!
  if (s.type === 'weight' && s.suggested_weight_kg != null) {
    const inc = s.increment != null ? ` (+${s.increment})` : ''
    return t('workout.rec_weight', { weight: s.suggested_weight_kg, inc })
  }
  if (s.type === 'reps' && s.suggested_reps != null) {
    return t('workout.rec_reps', { reps: s.suggested_reps })
  }
  return null
})

const weightValue = ref<number | null>(getInitialWeight())
const repsValue = ref<number | null>(getInitialReps())
const isLogged = ref(props.loggedSet !== null)

// Edit mode
const isEditing = ref(false)
const editWeight = ref<number | null>(null)
const editReps = ref<number | null>(null)

// Swipe reveal
const showActions = ref(false)
const rowEl = useTemplateRef<HTMLElement>('rowEl')

// An unlogged, non-extra set is a template set
const isTemplate = computed(() => !isLogged.value && !props.isExtra)

useSwipeLeft(rowEl, () => {
  showActions.value = true
})

// Update when loggedSet changes
watch(() => props.loggedSet, (newVal) => {
  if (newVal) {
    weightValue.value = newVal.weight_kg
    repsValue.value = newVal.reps
    isLogged.value = true
  } else {
    isLogged.value = false
    weightValue.value = getInitialWeight()
    repsValue.value = getInitialReps()
  }
})

function handleComplete() {
  if (isLogged.value) return
  emit('complete', {
    exercise_id: props.exerciseId,
    set_number: props.setNumber,
    weight_kg: weightValue.value,
    reps: repsValue.value,
    is_warmup: props.isWarmup,
  })
}

function enterEditMode() {
  if (!isLogged.value || !props.loggedSet) return
  editWeight.value = props.loggedSet.weight_kg
  editReps.value = props.loggedSet.reps
  isEditing.value = true
  showActions.value = false
}

function cancelEdit() {
  isEditing.value = false
}

function saveEdit() {
  if (!props.loggedSet) return
  emit('update', {
    setId: props.loggedSet.id,
    weight_kg: editWeight.value,
    reps: editReps.value,
  })
  isEditing.value = false
}

function saveInline() {
  if (!props.loggedSet) return
  if (weightValue.value === props.loggedSet.weight_kg && repsValue.value === props.loggedSet.reps) return
  emit('update', {
    setId: props.loggedSet.id,
    weight_kg: weightValue.value,
    reps: repsValue.value,
  })
}

function handleDelete() {
  showActions.value = false
  if (isTemplate.value) {
    emit('removeTemplate', { exerciseId: props.exerciseId, setNumber: props.setNumber })
    return
  }
  if (props.isExtra && !props.loggedSet) {
    emit('removeExtra', props.setNumber)
    return
  }
  if (!props.loggedSet) return
  emit('delete', props.loggedSet.id)
}

function parseNumber(val: string): number | null {
  const n = parseFloat(val)
  return isNaN(n) ? null : n
}
</script>

<template>
  <div ref="rowEl" class="relative overflow-hidden">
    <!-- Main row content -->
    <div
      class="flex items-center gap-2 px-3 py-2.5 rounded-lg min-h-[44px] transition-colors"
      :class="[
        isEditing ? 'bg-blue-50' : isLogged ? 'bg-green-50/60' : isWarmup ? 'bg-gray-50' : 'bg-white',
        !isLogged && 'cursor-pointer hover:bg-gray-50',
        isLogged && !isEditing && 'cursor-pointer'
      ]"
      @click="handleComplete"
    >
      <!-- Set number / warmup badge -->
      <div class="w-8 text-center flex-shrink-0">
        <span
          v-if="isWarmup"
          class="inline-block text-xs font-bold text-amber-600 bg-amber-100 rounded px-1.5 py-0.5"
        >
          W
        </span>
        <span v-else class="text-sm font-medium text-gray-400">{{ setNumber }}</span>
      </div>

      <!-- Edit mode -->
      <template v-if="isEditing">
        <input
          type="number"
          inputmode="decimal"
          :value="editWeight ?? ''"
          placeholder="--"
          class="w-16 text-center text-sm font-medium border border-blue-300 rounded-md py-1.5 focus:outline-none focus:border-blue-500"
          @click.stop
          @input="editWeight = parseNumber(($event.target as HTMLInputElement).value)"
        />
        <span class="text-xs text-gray-400 flex-shrink-0">kg</span>
        <span class="text-gray-300 flex-shrink-0">x</span>
        <input
          type="number"
          inputmode="numeric"
          :value="editReps ?? ''"
          placeholder="--"
          class="w-14 text-center text-sm font-medium border border-blue-300 rounded-md py-1.5 focus:outline-none focus:border-blue-500"
          @click.stop
          @input="editReps = parseNumber(($event.target as HTMLInputElement).value)"
        />
        <div class="flex-shrink-0 ml-auto flex items-center gap-1">
          <button
            class="px-2 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors"
            @click.stop="saveEdit"
          >
            Save
          </button>
          <button
            class="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            @click.stop="cancelEdit"
          >
            Cancel
          </button>
        </div>
      </template>

      <!-- Normal mode -->
      <template v-else>
        <div class="relative flex items-center">
          <input
            type="number"
            inputmode="decimal"
            :value="weightValue ?? ''"
            placeholder="--"
            class="w-16 text-center text-sm font-medium border rounded-md py-1.5 focus:outline-none"
            :class="[
              isLogged
                ? 'border-transparent bg-transparent text-gray-700 focus:border-blue-400 focus:bg-white'
                : 'border-gray-200 focus:border-blue-400',
              hasSuggestionIndicator && suggestionType === 'weight' && 'text-emerald-600 font-semibold border-emerald-300'
            ]"
            @click.stop
            @input="weightValue = parseNumber(($event.target as HTMLInputElement).value)"
            @blur="isLogged && saveInline()"
          />
          <!-- Suggestion arrow for weight -->
          <svg
            v-if="hasSuggestionIndicator && suggestionType === 'weight'"
            class="w-3.5 h-3.5 text-emerald-600 absolute -right-1 top-1/2 -translate-y-1/2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </div>
        <span class="text-xs text-gray-400 flex-shrink-0">kg</span>
        <span class="text-gray-300 flex-shrink-0">x</span>
        <div class="relative flex items-center">
          <input
            type="number"
            inputmode="numeric"
            :value="repsValue ?? ''"
            placeholder="--"
            class="w-14 text-center text-sm font-medium border rounded-md py-1.5 focus:outline-none"
            :class="[
              isLogged
                ? 'border-transparent bg-transparent text-gray-700 focus:border-blue-400 focus:bg-white'
                : 'border-gray-200 focus:border-blue-400',
              hasSuggestionIndicator && suggestionType === 'reps' && 'text-emerald-600 font-semibold border-emerald-300'
            ]"
            @click.stop
            @input="repsValue = parseNumber(($event.target as HTMLInputElement).value)"
            @blur="isLogged && saveInline()"
          />
          <!-- Suggestion arrow for reps -->
          <svg
            v-if="hasSuggestionIndicator && suggestionType === 'reps'"
            class="w-3.5 h-3.5 text-emerald-600 absolute -right-1 top-1/2 -translate-y-1/2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </div>

        <!-- Checkmark -->
        <div class="flex-shrink-0 ml-auto">
          <button
            v-if="!isLogged"
            class="w-8 h-8 flex items-center justify-center rounded-full border-2 border-gray-300 text-gray-400 hover:border-green-500 hover:text-green-500 transition-colors"
            @click.stop="handleComplete"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </button>
          <button
            v-else
            class="w-8 h-8 flex items-center justify-center rounded-full bg-green-500 text-white hover:bg-red-400 transition-colors"
            @click.stop="handleDelete"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </button>
        </div>
      </template>
    </div>

    <!-- Sub-line: "last time" reference (#1) + progression recommendation (#2) -->
    <div
      v-if="lastTimeText || recommendationText"
      class="pl-[3.25rem] pr-3 pb-1 -mt-0.5 text-[11px] leading-none select-none flex items-center gap-1.5 flex-wrap"
    >
      <span v-if="lastTimeText" class="text-gray-400">
        {{ t('workout.last_time') }} {{ lastTimeText }}
      </span>
      <span v-if="lastTimeText && recommendationText" class="text-gray-300">&middot;</span>
      <span v-if="recommendationText" class="text-emerald-600 font-medium">
        {{ recommendationText }}
      </span>
    </div>

    <!-- Swipe action buttons (revealed on swipe left) -->
    <Transition name="slide-actions">
      <div
        v-if="showActions"
        class="absolute right-0 top-0 bottom-0 flex items-stretch z-20"
      >
        <button
          v-if="isLogged"
          class="px-4 bg-blue-500 text-white text-xs font-medium hover:bg-blue-600 transition-colors"
          @click.stop="enterEditMode"
        >
          Edit
        </button>
        <button
          class="px-4 bg-red-500 text-white text-xs font-medium hover:bg-red-600 transition-colors"
          @click.stop="handleDelete"
        >
          Delete
        </button>
      </div>
    </Transition>

    <!-- Tap away to close actions -->
    <div
      v-if="showActions"
      class="absolute inset-0 z-10"
      @click="showActions = false"
    />
  </div>
</template>

<style scoped>
.slide-actions-enter-active,
.slide-actions-leave-active {
  transition: transform 0.2s ease;
}
.slide-actions-enter-from,
.slide-actions-leave-to {
  transform: translateX(100%);
}
</style>
