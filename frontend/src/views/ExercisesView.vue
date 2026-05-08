<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useExercisesStore } from '@/stores/exercises'
import { useDisplayName } from '@/composables/useDisplayName'
import type { Exercise } from '@/types'

const { t } = useI18n()
const { displayName } = useDisplayName()
const store = useExercisesStore()

// Filter state
const searchQuery = ref('')
const equipmentFilter = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// UI state
const collapsedGroups = ref<Set<string>>(new Set())
const addingToGroup = ref<string | null>(null)
const editingId = ref<string | null>(null)

// Create form state
const createForm = ref({ name: '', equipment: 'Barbell' })
const createError = ref('')
const createLoading = ref(false)

// Edit form state
const editForm = ref({ name: '', muscle_group: '', equipment: '' })
const editLoading = ref(false)

const EQUIPMENT_OPTIONS = ['Barbell', 'Dumbbell', 'Cable', 'Machine', 'Bodyweight', 'Other']

// Grouped exercises, sorted by muscle group
const groupedExercises = computed(() => {
  const groups: Record<string, Exercise[]> = {}
  for (const ex of store.exercises) {
    const group = ex.muscle_group
    if (!groups[group]) groups[group] = []
    groups[group].push(ex)
  }
  // Sort groups alphabetically, exercises within group alphabetically
  const sorted = Object.keys(groups).sort()
  return sorted.map((name) => ({
    name,
    exercises: groups[name].sort((a, b) => a.name.localeCompare(b.name)),
  }))
})

// Equipment options from loaded exercises (for filter dropdown)
const availableEquipment = computed(() => {
  const set = new Set(store.exercises.map((e) => e.equipment))
  return Array.from(set).sort()
})

// All known muscle groups (for edit dropdown)
const availableMuscleGroups = computed(() => {
  const set = new Set(store.exercises.map((e) => e.muscle_group))
  return Array.from(set).sort()
})

function isCollapsed(group: string): boolean {
  return collapsedGroups.value.has(group)
}

function toggleGroup(group: string) {
  if (collapsedGroups.value.has(group)) {
    collapsedGroups.value.delete(group)
  } else {
    collapsedGroups.value.add(group)
  }
}

// Auto-collapse large groups on initial load
function autoCollapseGroups() {
  for (const group of groupedExercises.value) {
    if (group.exercises.length > 8) {
      collapsedGroups.value.add(group.name)
    }
  }
}

// Search with debounce
function onSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchWithFilters()
  }, 300)
}

function onEquipmentChange() {
  fetchWithFilters()
}

function fetchWithFilters() {
  store.fetchExercises({
    search: searchQuery.value || undefined,
    equipment: equipmentFilter.value || undefined,
  })
}

// Create exercise
function startCreate(group: string) {
  addingToGroup.value = group
  createForm.value = { name: '', equipment: 'Barbell' }
  createError.value = ''
  editingId.value = null
}

function cancelCreate() {
  addingToGroup.value = null
  createError.value = ''
}

async function submitCreate() {
  if (!createForm.value.name.trim()) {
    createError.value = 'Name is required'
    return
  }
  if (!addingToGroup.value) return
  createLoading.value = true
  try {
    await store.createExercise({
      name: createForm.value.name.trim(),
      muscle_group: addingToGroup.value,
      equipment: createForm.value.equipment,
    })
    addingToGroup.value = null
    createError.value = ''
  } catch (e) {
    createError.value = e instanceof Error ? e.message : 'Failed to create exercise'
  } finally {
    createLoading.value = false
  }
}

// Edit exercise
function startEdit(exercise: Exercise) {
  editingId.value = exercise.id
  editForm.value = {
    name: exercise.name,
    muscle_group: exercise.muscle_group,
    equipment: exercise.equipment,
  }
  addingToGroup.value = null
}

function cancelEdit() {
  editingId.value = null
}

async function submitEdit() {
  if (editingId.value === null) return
  editLoading.value = true
  try {
    await store.updateExercise(editingId.value, {
      name: editForm.value.name.trim(),
      muscle_group: editForm.value.muscle_group,
      equipment: editForm.value.equipment,
    })
    editingId.value = null
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Failed to update exercise')
  } finally {
    editLoading.value = false
  }
}

// Delete exercise
async function confirmDelete(exercise: Exercise) {
  if (!window.confirm(`Delete "${exercise.name}"?`)) return
  try {
    await store.deleteExercise(exercise.id)
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Failed to delete exercise')
  }
}

onMounted(async () => {
  await store.fetchExercises()
  autoCollapseGroups()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-4">{{ t('exercises.title') }}</h1>

      <!-- Filters -->
      <div class="flex flex-col sm:flex-row gap-3">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('exercises.search_placeholder')"
          class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
          @input="onSearchInput"
        />
        <select
          v-model="equipmentFilter"
          class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-700"
          @change="onEquipmentChange"
        >
          <option value="">{{ t('exercises.all_equipment') }}</option>
          <option v-for="eq in availableEquipment" :key="eq" :value="eq">{{ eq }}</option>
        </select>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="store.loading" class="flex items-center justify-center py-12">
      <div class="h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <span class="ml-3 text-sm text-gray-500">{{ t('exercises.loading') }}</span>
    </div>

    <!-- Error state -->
    <div v-else-if="store.error" class="text-center py-12">
      <p class="text-sm text-red-600">{{ store.error }}</p>
      <button
        class="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium"
        @click="fetchWithFilters"
      >
        {{ t('exercises.try_again') }}
      </button>
    </div>

    <!-- Empty state -->
    <div v-else-if="groupedExercises.length === 0" class="text-center py-12">
      <p class="text-gray-500 text-sm">{{ t('exercises.empty_title') }}</p>
      <p class="text-gray-400 text-xs mt-1">{{ t('exercises.empty_hint') }}</p>
    </div>

    <!-- Grouped exercise list -->
    <div v-else class="space-y-4">
      <div
        v-for="group in groupedExercises"
        :key="group.name"
        class="bg-white rounded-lg border border-gray-200 overflow-hidden"
      >
        <!-- Group header -->
        <button
          class="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors text-left"
          @click="toggleGroup(group.name)"
        >
          <div class="flex items-center gap-2">
            <!-- Chevron -->
            <svg
              class="h-4 w-4 text-gray-400 transition-transform"
              :class="{ '-rotate-90': isCollapsed(group.name) }"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
            <span class="text-sm font-semibold text-gray-900">{{ t('muscle_groups.' + group.name) }}</span>
            <span class="text-xs text-gray-400 font-normal">{{ group.exercises.length }}</span>
          </div>
          <!-- Add button -->
          <span
            class="text-gray-400 hover:text-blue-600 text-lg font-light leading-none px-1"
            :title="t('exercises.add_custom_title')"
            @click.stop="startCreate(group.name)"
          >+</span>
        </button>

        <!-- Group body -->
        <div v-show="!isCollapsed(group.name)">
          <!-- Inline create form -->
          <div v-if="addingToGroup === group.name" class="px-4 py-3 bg-blue-50 border-t border-gray-200">
            <div class="flex flex-col sm:flex-row gap-2">
              <input
                v-model="createForm.name"
                type="text"
                :placeholder="t('exercises.name_placeholder')"
                class="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                @keyup.enter="submitCreate"
              />
              <select
                v-model="createForm.equipment"
                class="px-3 py-1.5 border border-gray-300 rounded text-sm bg-white"
              >
                <option v-for="eq in EQUIPMENT_OPTIONS" :key="eq" :value="eq">{{ eq }}</option>
              </select>
              <div class="flex gap-1">
                <button
                  class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                  :disabled="createLoading"
                  @click="submitCreate"
                >
                  {{ t('exercises.add') }}
                </button>
                <button
                  class="px-3 py-1.5 text-gray-600 rounded text-sm font-medium hover:bg-gray-100"
                  @click="cancelCreate"
                >
                  {{ t('exercises.cancel') }}
                </button>
              </div>
            </div>
            <p v-if="createError" class="text-xs text-red-600 mt-1">{{ createError }}</p>
          </div>

          <!-- Exercise list -->
          <ul class="divide-y divide-gray-100">
            <li v-for="exercise in group.exercises" :key="exercise.id">
              <!-- Edit form (inline replacement) -->
              <div v-if="editingId === exercise.id" class="px-4 py-3 bg-yellow-50">
                <div class="flex flex-col sm:flex-row gap-2">
                  <input
                    v-model="editForm.name"
                    type="text"
                    class="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    @keyup.enter="submitEdit"
                  />
                  <select
                    v-model="editForm.muscle_group"
                    class="px-3 py-1.5 border border-gray-300 rounded text-sm bg-white"
                  >
                    <option v-for="mg in availableMuscleGroups" :key="mg" :value="mg">{{ mg }}</option>
                  </select>
                  <select
                    v-model="editForm.equipment"
                    class="px-3 py-1.5 border border-gray-300 rounded text-sm bg-white"
                  >
                    <option v-for="eq in EQUIPMENT_OPTIONS" :key="eq" :value="eq">{{ eq }}</option>
                  </select>
                  <div class="flex gap-1">
                    <button
                      class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                      :disabled="editLoading"
                      @click="submitEdit"
                    >
                      {{ t('exercises.save') }}
                    </button>
                    <button
                      class="px-3 py-1.5 text-gray-600 rounded text-sm font-medium hover:bg-gray-100"
                      @click="cancelEdit"
                    >
                      {{ t('exercises.cancel') }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Normal exercise row -->
              <div v-else class="group flex items-center justify-between px-4 py-2.5 hover:bg-gray-50">
                <div class="flex items-center gap-2 min-w-0">
                  <RouterLink
                    :to="'/exercises/' + exercise.id + '/history'"
                    class="text-sm text-gray-900 truncate hover:text-blue-600 hover:underline transition-colors"
                  >{{ displayName(exercise) }}</RouterLink>
                  <span class="text-xs text-gray-400 shrink-0">{{ exercise.equipment }}</span>
                  <span
                    v-if="exercise.is_custom"
                    class="text-xs font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded shrink-0"
                  >
                    {{ t('exercises.custom_badge') }}
                  </span>
                </div>
                <!-- Actions for custom exercises -->
                <div
                  v-if="exercise.is_custom"
                  class="flex gap-1 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity shrink-0"
                >
                  <button
                    class="p-1 text-gray-400 hover:text-blue-600 rounded"
                    title="Edit"
                    @click="startEdit(exercise)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </button>
                  <button
                    class="p-1 text-gray-400 hover:text-red-600 rounded"
                    title="Delete"
                    @click="confirmDelete(exercise)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
