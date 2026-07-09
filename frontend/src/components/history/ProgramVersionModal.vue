<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useProgramsStore } from '@/stores/programs'
import { useDisplayName } from '@/composables/useDisplayName'
import type { ProgramVersionSnapshot } from '@/types'

const props = defineProps<{
  programId: string
  version: number
}>()

const emit = defineEmits<{
  close: []
}>()

const { t } = useI18n()
const programsStore = useProgramsStore()
const { displayName } = useDisplayName()

const snapshot = ref<ProgramVersionSnapshot | null>(null)
const loading = ref(true)
const error = ref(false)

function formatTarget(reps: number, weight_kg: number | null): string {
  const w = weight_kg !== null ? `${weight_kg}${t('summary.kg')}` : t('history.bodyweight')
  return `${w} x ${reps} ${t('history.reps_short')}`
}

onMounted(async () => {
  try {
    snapshot.value = await programsStore.fetchProgramVersion(props.programId, props.version)
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
    <div class="bg-white rounded-lg shadow-lg w-full max-w-md max-h-[80vh] overflow-y-auto">
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h2 class="text-sm font-semibold text-gray-900">
          {{ snapshot ? snapshot.name : t('history.version_view_title', { n: version }) }}
        </h2>
        <button
          data-testid="version-modal-close"
          class="text-gray-400 hover:text-gray-600 transition-colors"
          :aria-label="t('history.version_close')"
          @click="emit('close')"
        >
          <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div v-if="loading" class="flex items-center justify-center py-10">
        <div class="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span class="ml-3 text-sm text-gray-500">{{ t('history.version_loading') }}</span>
      </div>

      <div v-else-if="error" class="px-4 py-6 text-center text-sm text-red-600">
        {{ t('history.version_failed') }}
      </div>

      <div v-else-if="snapshot" class="px-4 py-3 space-y-3">
        <span
          v-if="snapshot.is_current"
          class="inline-block text-[10px] font-medium text-green-700 bg-green-50 rounded-full px-1.5 py-0.5"
        >
          {{ t('history.version_current') }}
        </span>

        <div v-for="ex in snapshot.exercises" :key="ex.exercise_id">
          <p class="text-sm font-medium text-gray-800">
            {{ ex.exercise ? displayName(ex.exercise) : ex.exercise_id }}
          </p>
          <ul class="mt-1 space-y-0.5">
            <li
              v-for="s in ex.sets"
              :key="s.set_number"
              class="text-xs text-gray-600 flex items-center gap-1"
            >
              <span class="text-gray-400 w-12">{{ t('programs.set_n', { n: s.set_number }) }}</span>
              <span>{{ formatTarget(s.target_reps, s.target_weight_kg) }}</span>
              <span v-if="s.is_warmup" class="text-gray-400 text-[10px]">{{ t('history.warmup_short') }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
