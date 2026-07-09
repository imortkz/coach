<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useHistoryStore } from '@/stores/history'
import { useProgramsStore } from '@/stores/programs'
import WorkoutCard from '@/components/history/WorkoutCard.vue'
import ProgramVersionModal from '@/components/history/ProgramVersionModal.vue'

const { t } = useI18n()
const historyStore = useHistoryStore()
const programsStore = useProgramsStore()

// Track expanded workout IDs
const expandedIds = ref<Set<string>>(new Set())

// Program-version snapshot modal (M010)
const viewingVersion = ref<{ programId: string; version: number } | null>(null)

function onViewVersion(programId: string, version: number) {
  viewingVersion.value = { programId, version }
}

// Initial load state (vs. load-more)
const initialLoading = ref(true)

// Program name lookup
const programNameMap = computed(() => {
  const map = new Map<string, string>()
  for (const p of programsStore.programs) {
    map.set(p.id, p.name)
  }
  return map
})

function getProgramName(programId: string | null): string {
  if (programId === null) return ''
  return programNameMap.value.get(programId) || t('history.unknown_program')
}

function toggleExpand(id: string) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
}

async function onDeleteWorkout(id: string) {
  if (!confirm(t('history.delete_confirm'))) return
  try {
    await historyStore.deleteWorkout(id)
    expandedIds.value.delete(id)
  } catch (e) {
    alert(e instanceof Error ? e.message : t('history.failed_delete'))
  }
}

function onFilterChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  const programId = value === '' ? null : value
  expandedIds.value.clear()
  historyStore.setFilter(programId)
}

async function loadMore() {
  await historyStore.loadWorkouts()
}

onMounted(async () => {
  // Fetch programs for name lookup and filter dropdown
  if (programsStore.programs.length === 0) {
    await programsStore.fetchPrograms()
  }
  await historyStore.loadWorkouts(true)
  initialLoading.value = false
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-4">{{ t('history.title') }}</h1>

      <!-- Program filter -->
      <select
        :value="historyStore.programFilter ?? ''"
        class="w-full sm:w-auto px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-700"
        @change="onFilterChange"
      >
        <option value="">{{ t('history.all_programs') }}</option>
        <option
          v-for="program in programsStore.programs"
          :key="program.id"
          :value="program.id"
        >
          {{ program.name }}
        </option>
      </select>
    </div>

    <!-- Loading state (initial load) -->
    <div v-if="initialLoading" class="flex items-center justify-center py-12">
      <div class="h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <span class="ml-3 text-sm text-gray-500">{{ t('history.loading') }}</span>
    </div>

    <!-- Empty state -->
    <div v-else-if="historyStore.workouts.length === 0" class="text-center py-12">
      <p class="text-gray-500 text-sm">{{ t('history.empty') }}</p>
      <p class="text-gray-400 text-xs mt-1">{{ t('history.empty_hint') }}</p>
    </div>

    <!-- Workout list -->
    <div v-else class="space-y-3">
      <WorkoutCard
        v-for="workout in historyStore.workouts"
        :key="workout.id"
        :workout="workout"
        :expanded="expandedIds.has(workout.id)"
        :program-name="getProgramName(workout.program_id)"
        @toggle="toggleExpand(workout.id)"
        @delete="onDeleteWorkout(workout.id)"
        @view-version="onViewVersion"
      />

      <!-- Load more button -->
      <div v-if="historyStore.hasMore" class="flex justify-center pt-2 pb-4">
        <button
          class="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="historyStore.loading"
          @click="loadMore"
        >
          {{ historyStore.loading ? t('history.loading_more') : t('history.load_more') }}
        </button>
      </div>
    </div>

    <ProgramVersionModal
      v-if="viewingVersion"
      :program-id="viewingVersion.programId"
      :version="viewingVersion.version"
      @close="viewingVersion = null"
    />
  </div>
</template>
