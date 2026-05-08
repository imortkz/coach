<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Bar } from 'vue-chartjs'
import {
  Chart,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { useReportStore } from '@/stores/report'

Chart.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const { t } = useI18n()
const store = useReportStore()

const WEEK_OPTIONS = [2, 4, 8] as const

// Muscle-group colors — kept stable across renders so the same group is the
// same color in the legend over time. Order doesn't matter, only consistency.
const MUSCLE_COLORS: Record<string, string> = {
  Chest: '#EF4444',
  Back: '#3B82F6',
  Legs: '#10B981',
  Shoulders: '#F59E0B',
  Arms: '#8B5CF6',
  Core: '#EC4899',
  Other: '#6B7280',
}

function colorFor(muscle: string): string {
  return MUSCLE_COLORS[muscle] ?? '#6B7280'
}

const muscleGroups = computed(() => {
  if (!store.report) return []
  const seen = new Set<string>()
  for (const entry of store.report.volume_by_week) seen.add(entry.muscle_group)
  return Array.from(seen).sort()
})

const volumeChartData = computed(() => {
  const r = store.report
  if (!r) return { labels: [], datasets: [] }

  const lookup = new Map<string, number>()
  for (const entry of r.volume_by_week) {
    lookup.set(`${entry.week}|${entry.muscle_group}`, entry.volume_kg)
  }

  return {
    labels: r.weeks,
    datasets: muscleGroups.value.map((mg) => ({
      label: t(`muscle_groups.${mg}`, mg),
      data: r.weeks.map((w) => lookup.get(`${w}|${mg}`) ?? 0),
      backgroundColor: colorFor(mg),
      stack: 'volume',
    })),
  }
})

const volumeChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  scales: {
    x: { stacked: true, grid: { display: false } },
    y: {
      stacked: true,
      title: { display: true, text: t('report.volume_axis'), font: { size: 11 } },
      grid: { color: 'rgba(0, 0, 0, 0.06)' },
    },
  },
  plugins: {
    legend: { position: 'bottom' as const, labels: { usePointStyle: true, padding: 12, font: { size: 12 } } },
    tooltip: { mode: 'index' as const, intersect: false },
  },
}))

const frequencyChartData = computed(() => {
  const r = store.report
  if (!r) return { labels: [], datasets: [] }
  return {
    labels: r.frequency_by_week.map((e) => e.week),
    datasets: [
      {
        label: t('report.workouts_per_week'),
        data: r.frequency_by_week.map((e) => e.count),
        backgroundColor: '#3B82F6',
      },
    ],
  }
})

const frequencyChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  scales: {
    x: { grid: { display: false } },
    y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: 'rgba(0, 0, 0, 0.06)' } },
  },
  plugins: {
    legend: { display: false },
    tooltip: { mode: 'index' as const, intersect: false },
  },
}))

const hasVolume = computed(() => (store.report?.volume_by_week.length ?? 0) > 0)
const hasPRs = computed(() => (store.report?.personal_records.length ?? 0) > 0)
const hasAnyWorkouts = computed(() =>
  (store.report?.frequency_by_week ?? []).some((e) => e.count > 0)
)

function changeWeeks(n: number) {
  if (n === store.weeks) return
  store.load(n)
}

onMounted(() => {
  store.load()
})
</script>

<template>
  <div class="space-y-6">
    <header class="flex items-center justify-between flex-wrap gap-3">
      <h1 class="text-2xl font-bold text-gray-900">{{ t('report.title') }}</h1>
      <div class="flex gap-1 bg-white border border-gray-200 rounded-lg p-1" role="group">
        <button
          v-for="n in WEEK_OPTIONS"
          :key="n"
          type="button"
          class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
          :class="
            store.weeks === n
              ? 'bg-blue-600 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          "
          @click="changeWeeks(n)"
        >
          {{ t('report.weeks_n', { n }) }}
        </button>
      </div>
    </header>

    <p v-if="store.loading" class="text-gray-500 text-sm">{{ t('report.loading') }}</p>
    <p v-else-if="store.error" class="text-red-600 text-sm">{{ store.error }}</p>

    <template v-else-if="store.report">
      <section class="bg-white rounded-lg border border-gray-200 p-4">
        <h2 class="text-base font-semibold text-gray-900 mb-3">
          {{ t('report.section_volume') }}
        </h2>
        <Bar v-if="hasVolume" :data="volumeChartData" :options="volumeChartOptions" />
        <p v-else class="text-gray-500 text-sm py-6 text-center">
          {{ t('report.empty_volume') }}
        </p>
      </section>

      <section class="bg-white rounded-lg border border-gray-200 p-4">
        <h2 class="text-base font-semibold text-gray-900 mb-3">
          {{ t('report.section_frequency') }}
        </h2>
        <Bar
          v-if="hasAnyWorkouts"
          :data="frequencyChartData"
          :options="frequencyChartOptions"
        />
        <p v-else class="text-gray-500 text-sm py-6 text-center">
          {{ t('report.empty_frequency') }}
        </p>
      </section>

      <section class="bg-white rounded-lg border border-gray-200 p-4">
        <h2 class="text-base font-semibold text-gray-900 mb-3">
          {{ t('report.section_prs') }}
        </h2>
        <table v-if="hasPRs" class="w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 border-b border-gray-200">
              <th class="py-2 font-medium">{{ t('report.col_exercise') }}</th>
              <th class="py-2 font-medium text-right">{{ t('report.col_period_best') }}</th>
              <th class="py-2 font-medium text-right">{{ t('report.col_previous_best') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="pr in store.report.personal_records"
              :key="pr.exercise_name"
              class="border-b border-gray-100 last:border-0"
            >
              <td class="py-2">
                <span>{{ pr.exercise_name }}</span>
                <span
                  v-if="pr.is_new_pr"
                  class="ml-2 inline-block bg-green-100 text-green-700 text-xs font-semibold px-2 py-0.5 rounded"
                >
                  {{ t('report.badge_new_pr') }}
                </span>
              </td>
              <td class="py-2 text-right tabular-nums">{{ pr.best_weight_in_period }} kg</td>
              <td class="py-2 text-right tabular-nums text-gray-500">
                <template v-if="pr.previous_best !== null">{{ pr.previous_best }} kg</template>
                <template v-else>—</template>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="text-gray-500 text-sm py-6 text-center">
          {{ t('report.empty_prs') }}
        </p>
      </section>
    </template>
  </div>
</template>
