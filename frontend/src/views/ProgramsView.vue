<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useProgramsStore } from '@/stores/programs'

const store = useProgramsStore()

onMounted(() => {
  store.fetchPrograms()
})

const programs = computed(() => store.programs)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString()
}

async function handleDelete(id: number, name: string) {
  if (!confirm(`Delete program "${name}"? This cannot be undone.`)) return
  try {
    await store.deleteProgram(id)
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Failed to delete program')
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Programs</h1>
      <router-link
        to="/programs/new"
        class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
      >
        New Program
      </router-link>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">
      Loading programs...
    </div>

    <div v-else-if="programs.length === 0" class="text-center py-12">
      <p class="text-gray-500 mb-4">No programs yet. Create your first program.</p>
      <router-link
        to="/programs/new"
        class="text-blue-600 hover:text-blue-700 font-medium"
      >
        Create a program
      </router-link>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="program in programs"
        :key="program.id"
        class="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
      >
        <div class="flex items-center justify-between">
          <div>
            <h2 class="font-semibold text-gray-900">{{ program.name }}</h2>
            <p class="text-sm text-gray-500 mt-1">
              {{ program.exercises.length }} exercise{{ program.exercises.length !== 1 ? 's' : '' }}
              <span class="mx-1">&middot;</span>
              Created {{ formatDate(program.created_at) }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <router-link
              :to="`/programs/${program.id}/edit`"
              class="px-3 py-1.5 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Edit
            </router-link>
            <button
              @click="handleDelete(program.id, program.name)"
              class="px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-md hover:bg-red-50 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
