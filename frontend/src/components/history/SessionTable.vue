<script setup lang="ts">
import type { ExerciseSession } from '@/types'

defineProps<{
  sessions: ExerciseSession[]
}>()

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

function formatWeight(kg: number | null): string {
  return kg !== null ? `${kg}kg` : 'BW'
}
</script>

<template>
  <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 bg-gray-50/80">
          <th class="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Date</th>
          <th class="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Sets</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(session, idx) in sessions"
          :key="idx"
          class="border-b border-gray-100 last:border-0"
          :class="idx % 2 === 1 ? 'bg-gray-50/40' : ''"
        >
          <td class="px-4 py-2.5 text-gray-700 whitespace-nowrap align-top font-medium">
            {{ formatDate(session.date) }}
          </td>
          <td class="px-4 py-2.5">
            <div class="flex flex-wrap gap-x-3 gap-y-0.5">
              <span
                v-for="set in session.sets"
                :key="set.set_number"
                class="whitespace-nowrap"
                :class="set.is_warmup ? 'text-gray-400' : 'text-gray-700'"
              >
                <template v-if="set.is_warmup">(W) </template>
                {{ formatWeight(set.weight_kg) }} x {{ set.reps ?? '--' }}
              </span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
