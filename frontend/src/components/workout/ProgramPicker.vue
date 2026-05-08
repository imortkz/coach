<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useProgramsStore } from '@/stores/programs'

const emit = defineEmits<{
  select: [programId: number]
}>()

const store = useProgramsStore()

onMounted(() => {
  store.fetchPrograms()
})

const programs = computed(() => store.programs)
const loading = computed(() => store.loading)

function totalSets(program: typeof programs.value[0]): number {
  return program.exercises.reduce((sum, ex) => sum + ex.sets.length, 0)
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Start Workout</h1>
    <p class="text-gray-500 text-sm mb-6">Choose a program to begin.</p>

    <div v-if="loading" class="text-center py-12 text-gray-500">
      Loading programs...
    </div>

    <div v-else-if="programs.length === 0" class="text-center py-12">
      <p class="text-gray-500 mb-4">No programs yet. Create one first.</p>
      <router-link
        to="/programs/new"
        class="text-blue-600 hover:text-blue-700 font-medium"
      >
        Create a program
      </router-link>
    </div>

    <div v-else class="space-y-3">
      <button
        v-for="program in programs"
        :key="program.id"
        class="w-full text-left border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:bg-blue-50/50 transition-colors active:bg-blue-50"
        @click="emit('select', program.id)"
      >
        <h2 class="font-semibold text-gray-900">{{ program.name }}</h2>
        <p class="text-sm text-gray-500 mt-1">
          {{ program.exercises.length }} exercise{{ program.exercises.length !== 1 ? 's' : '' }}
          <span class="mx-1">&middot;</span>
          {{ totalSets(program) }} set{{ totalSets(program) !== 1 ? 's' : '' }}
        </p>
      </button>
    </div>
  </div>
</template>
