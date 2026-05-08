<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWorkoutsStore } from '@/stores/workouts'
import ProgramPicker from '@/components/workout/ProgramPicker.vue'
import ActiveWorkout from '@/components/workout/ActiveWorkout.vue'

const { t } = useI18n()
const workoutsStore = useWorkoutsStore()
const activeWorkoutRef = ref<InstanceType<typeof ActiveWorkout> | null>(null)

const loading = computed(() => workoutsStore.loading)
const hasActiveWorkout = computed(() =>
  workoutsStore.activeWorkout !== null || activeWorkoutRef.value?.discarding
)
const error = computed(() => workoutsStore.error)

onMounted(async () => {
  await workoutsStore.fetchActiveWorkout()
})

onBeforeUnmount(() => {
  // Flush any pending undo deletes on navigation
  activeWorkoutRef.value?.flushPendingDeletes()
})

async function onStartWorkout(programId: number) {
  try {
    await workoutsStore.startWorkout(programId)
  } catch {
    // error is set in store
  }
}
</script>

<template>
  <div>
    <div v-if="error" class="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>

    <div v-if="loading && !hasActiveWorkout" class="text-center py-12 text-gray-500">
      {{ t('workout.loading') }}
    </div>

    <ActiveWorkout v-else-if="hasActiveWorkout" ref="activeWorkoutRef" />

    <ProgramPicker v-else @select="onStartWorkout" />
  </div>
</template>
