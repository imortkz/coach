<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import type { ExerciseSession } from '@/types'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps<{
  sessions: ExerciseSession[]
}>()

const chartData = computed(() => {
  // Display chronologically (oldest first)
  const sorted = [...props.sessions].reverse()

  return {
    labels: sorted.map((s) =>
      new Date(s.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    ),
    datasets: [
      {
        label: 'Best Set Weight (kg)',
        data: sorted.map((s) => s.best_weight),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.3,
        yAxisID: 'y',
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Total Volume',
        data: sorted.map((s) => s.total_volume),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.3,
        yAxisID: 'y1',
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  scales: {
    y: {
      type: 'linear' as const,
      position: 'left' as const,
      title: {
        display: true,
        text: 'Weight (kg)',
        font: { size: 11 },
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.06)',
      },
    },
    y1: {
      type: 'linear' as const,
      position: 'right' as const,
      title: {
        display: true,
        text: 'Volume',
        font: { size: 11 },
      },
      grid: {
        drawOnChartArea: false,
      },
    },
  },
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        usePointStyle: true,
        padding: 16,
        font: { size: 12 },
      },
    },
  },
}))
</script>

<template>
  <div class="bg-white rounded-lg border border-gray-200 p-4">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
