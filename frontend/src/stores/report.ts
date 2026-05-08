import { apiFetch } from '@/lib/apiFetch'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { ReportResponse } from '@/types'

const API_BASE = '/api/workouts/report'

export const useReportStore = defineStore('report', () => {
  const report = ref<ReportResponse | null>(null)
  const weeks = ref<number>(4)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load(weeksValue: number = weeks.value) {
    loading.value = true
    error.value = null
    weeks.value = weeksValue
    try {
      const res = await apiFetch(`${API_BASE}?weeks=${weeksValue}`)
      if (!res.ok) throw new Error(`Failed to fetch report: ${res.status} ${res.statusText}`)
      report.value = (await res.json()) as ReportResponse
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      report.value = null
    } finally {
      loading.value = false
    }
  }

  return { report, weeks, loading, error, load }
})
