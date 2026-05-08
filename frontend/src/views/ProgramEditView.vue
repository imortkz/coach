<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProgramsStore } from '@/stores/programs'
import { useExercisesStore } from '@/stores/exercises'
import { useDisplayName } from '@/composables/useDisplayName'
import type { Exercise } from '@/types'
import type { ProgramCreatePayload } from '@/stores/programs'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { displayName } = useDisplayName()
const programsStore = useProgramsStore()
const exercisesStore = useExercisesStore()

const isEditMode = computed(() => !!route.params.id)
// route.params.id is the UUID string from the URL — keep it as-is.
// Casting to Number() turns the UUID into NaN, which is what the
// previous version did and is the root cause of issue #20.
const programId = computed(() => String(route.params.id))

// Form state
const programName = ref('')
const restTimerDisabled = ref(false)
const exercises = ref<BuilderExercise[]>([])
const saving = ref(false)
const loadingProgram = ref(false)
const formError = ref<string | null>(null)

// Exercise picker state
const showPicker = ref(false)
const searchQuery = ref('')

interface BuilderSet {
  target_reps: number
  target_weight_kg: number | null
  is_warmup: boolean
}

// Carry the full Exercise object so displayName() stays reactive when the
// user toggles language mid-session. exercise_name as a plain string would
// freeze at the moment of addExercise(); see M007-ROADMAP.md S02.
interface BuilderExercise {
  exercise: Exercise
  sets: BuilderSet[]
}

const filteredExercises = computed(() => {
  if (!searchQuery.value.trim()) return exercisesStore.exercises
  const q = searchQuery.value.toLowerCase()
  // Search both English and Russian names so the picker works regardless
  // of the active locale.
  return exercisesStore.exercises.filter((ex: Exercise) =>
    ex.name.toLowerCase().includes(q) ||
    (ex.name_ru?.toLowerCase().includes(q) ?? false)
  )
})

function defaultSets(): BuilderSet[] {
  return [
    { target_reps: 10, target_weight_kg: null, is_warmup: false },
    { target_reps: 10, target_weight_kg: null, is_warmup: false },
    { target_reps: 10, target_weight_kg: null, is_warmup: false },
  ]
}

function addExercise(ex: Exercise) {
  exercises.value.push({
    exercise: ex,
    sets: defaultSets(),
  })
  showPicker.value = false
  searchQuery.value = ''
}

function removeExercise(index: number) {
  exercises.value.splice(index, 1)
}

function moveExercise(index: number, direction: -1 | 1) {
  const target = index + direction
  if (target < 0 || target >= exercises.value.length) return
  const temp = exercises.value[index]
  exercises.value[index] = exercises.value[target]
  exercises.value[target] = temp
}

function addSet(exerciseIndex: number) {
  exercises.value[exerciseIndex].sets.push({
    target_reps: 10,
    target_weight_kg: null,
    is_warmup: false,
  })
}

function removeSet(exerciseIndex: number, setIndex: number) {
  exercises.value[exerciseIndex].sets.splice(setIndex, 1)
}

function validate(): string | null {
  if (!programName.value.trim()) return t('programs.name_required')
  if (exercises.value.length === 0) return t('programs.add_at_least_one_exercise')
  for (let i = 0; i < exercises.value.length; i++) {
    if (exercises.value[i].sets.length === 0) {
      return t('programs.needs_at_least_one_set', { name: displayName(exercises.value[i].exercise) })
    }
  }
  return null
}

function buildPayload(): ProgramCreatePayload {
  return {
    name: programName.value.trim(),
    rest_timer_disabled: restTimerDisabled.value,
    exercises: exercises.value.map((ex, i) => ({
      exercise_id: ex.exercise.id,
      order: i + 1,
      sets: ex.sets.map((s, si) => ({
        set_number: si + 1,
        target_reps: s.target_reps,
        target_weight_kg: s.target_weight_kg,
        is_warmup: s.is_warmup,
      })),
    })),
  }
}

async function handleSave() {
  const validationError = validate()
  if (validationError) {
    formError.value = validationError
    return
  }
  formError.value = null
  saving.value = true
  try {
    const payload = buildPayload()
    if (isEditMode.value) {
      await programsStore.updateProgram(programId.value, payload)
    } else {
      await programsStore.createProgram(payload)
    }
    router.push('/programs')
  } catch (e) {
    formError.value = e instanceof Error ? e.message : t('programs.failed_save')
  } finally {
    saving.value = false
  }
}

// Edit-mode hydration falls back to a synthetic Exercise stub when the
// referenced exercise has been deleted from the master list — keeps the
// editor functional and identifies the gap to the user.
function syntheticExercise(id: string): Exercise {
  return {
    id,
    name: `Exercise #${id}`,
    muscle_group: '',
    equipment: '',
    is_custom: false,
    name_ru: null,
    gif_url: null,
  }
}

onMounted(async () => {
  // Fetch all exercises for the picker
  await exercisesStore.fetchExercises()

  // If edit mode, load existing program
  if (isEditMode.value) {
    loadingProgram.value = true
    try {
      const program = await programsStore.fetchProgram(programId.value)
      programName.value = program.name
      restTimerDisabled.value = (program as any).rest_timer_disabled ?? false
      exercises.value = program.exercises
        .sort((a, b) => a.order - b.order)
        .map((pe) => ({
          exercise: pe.exercise ?? syntheticExercise(pe.exercise_id),
          sets: pe.sets
            .sort((a, b) => a.set_number - b.set_number)
            .map((s) => ({
              target_reps: s.target_reps,
              target_weight_kg: s.target_weight_kg,
              is_warmup: s.is_warmup,
            })),
        }))
    } catch (e) {
      formError.value = e instanceof Error ? e.message : t('programs.failed_load')
    } finally {
      loadingProgram.value = false
    }
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">
      {{ isEditMode ? t('programs.edit') : t('programs.new') }}
    </h1>

    <div v-if="loadingProgram" class="text-center py-12 text-gray-500">
      {{ t('programs.loading_one') }}
    </div>

    <div v-else>
      <!-- Error banner -->
      <div v-if="formError" class="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
        {{ formError }}
      </div>

      <!-- Program name -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('programs.name_label') }}</label>
        <input
          v-model="programName"
          type="text"
          :placeholder="t('programs.name_placeholder')"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <!-- Rest timer toggle -->
      <label class="flex items-center gap-2 mb-6 cursor-pointer">
        <input v-model="restTimerDisabled" type="checkbox"
          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
        <span class="text-sm text-gray-700">{{ t('programs.disable_rest_timer') }}</span>
      </label>

      <!-- Exercise list -->
      <div class="mb-6">
        <h2 class="text-sm font-medium text-gray-700 mb-3">{{ t('programs.exercises_section') }}</h2>

        <div v-if="exercises.length === 0" class="text-center py-8 text-gray-400 text-sm border border-dashed border-gray-300 rounded-lg">
          {{ t('programs.no_exercises_added') }}
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="(ex, exIdx) in exercises"
            :key="exIdx"
            class="border border-gray-200 rounded-lg overflow-hidden"
          >
            <!-- Exercise header -->
            <div class="flex items-center justify-between px-4 py-3 bg-gray-50">
              <div>
                <span class="font-medium text-gray-900 text-sm">{{ displayName(ex.exercise) }}</span>
                <span v-if="ex.exercise.equipment" class="ml-2 text-xs px-2 py-0.5 bg-gray-200 text-gray-600 rounded-full">
                  {{ ex.exercise.equipment }}
                </span>
              </div>
              <div class="flex items-center gap-1">
                <button
                  @click="moveExercise(exIdx, -1)"
                  :disabled="exIdx === 0"
                  class="p-1.5 text-gray-400 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                  :title="t('programs.move_up')"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
                <button
                  @click="moveExercise(exIdx, 1)"
                  :disabled="exIdx === exercises.length - 1"
                  class="p-1.5 text-gray-400 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                  :title="t('programs.move_down')"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
                <button
                  @click="removeExercise(exIdx)"
                  class="p-1.5 text-red-400 hover:text-red-600 ml-1"
                  :title="t('programs.remove_exercise_title')"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Sets -->
            <div class="px-4 py-3">
              <div class="space-y-2">
                <div
                  v-for="(set, setIdx) in ex.sets"
                  :key="setIdx"
                  class="flex items-center gap-3 text-sm"
                >
                  <span class="text-gray-500 w-12 shrink-0">{{ t('programs.set_n', { n: setIdx + 1 }) }}</span>

                  <div class="flex items-center gap-1">
                    <input
                      v-model.number="set.target_reps"
                      type="number"
                      min="1"
                      class="w-16 px-2 py-1 border border-gray-300 rounded text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <span class="text-gray-400 text-xs">{{ t('programs.reps') }}</span>
                  </div>

                  <div class="flex items-center gap-1">
                    <input
                      :value="set.target_weight_kg ?? ''"
                      @input="(e) => set.target_weight_kg = (e.target as HTMLInputElement).value === '' ? null : Number((e.target as HTMLInputElement).value)"
                      type="number"
                      min="0"
                      step="0.5"
                      placeholder="-"
                      class="w-20 px-2 py-1 border border-gray-300 rounded text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <span class="text-gray-400 text-xs">{{ t('programs.kg') }}</span>
                  </div>

                  <label class="flex items-center gap-1 cursor-pointer">
                    <input
                      v-model="set.is_warmup"
                      type="checkbox"
                      class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span class="text-gray-500 text-xs">{{ t('programs.warmup') }}</span>
                  </label>

                  <button
                    @click="removeSet(exIdx, setIdx)"
                    class="p-1 text-gray-300 hover:text-red-500 ml-auto"
                    :title="t('programs.remove_set_title')"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>

              <button
                @click="addSet(exIdx)"
                class="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                + {{ t('programs.add_set') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Add Exercise button / picker -->
        <div class="mt-4">
          <button
            v-if="!showPicker"
            @click="showPicker = true"
            class="w-full py-2.5 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
          >
            + {{ t('programs.add_exercise') }}
          </button>

          <div v-else class="border border-gray-300 rounded-lg p-3">
            <div class="flex items-center gap-2 mb-2">
              <input
                :value="searchQuery"
                @input="searchQuery = ($event.target as HTMLInputElement).value"
                type="text"
                :placeholder="t('exercises.search_placeholder')"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                ref="searchInput"
              />
              <button
                @click="showPicker = false; searchQuery = ''"
                class="px-3 py-2 text-sm text-gray-500 hover:text-gray-700"
              >
                {{ t('programs.cancel') }}
              </button>
            </div>

            <div class="max-h-48 overflow-y-auto">
              <div v-if="filteredExercises.length === 0" class="py-3 text-center text-gray-400 text-sm">
                {{ t('exercises.empty_title') }}
              </div>
              <button
                v-for="ex in filteredExercises"
                :key="ex.id"
                @click="addExercise(ex)"
                class="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 rounded transition-colors flex items-center justify-between"
              >
                <span class="text-gray-900">{{ displayName(ex) }}</span>
                <span class="text-xs text-gray-400">{{ ex.equipment }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3">
        <button
          @click="handleSave"
          :disabled="saving"
          class="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ saving ? t('programs.saving') : t('programs.save') }}
        </button>
        <router-link
          to="/programs"
          class="px-6 py-2.5 text-gray-600 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          {{ t('programs.cancel') }}
        </router-link>
      </div>
    </div>
  </div>
</template>
