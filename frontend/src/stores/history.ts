import { apiFetch } from '@/lib/apiFetch'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Workout } from '@/types'

const API_BASE = '/api/workouts'
const LIMIT = 20

export const useHistoryStore = defineStore('history', () => {
  const workouts = ref<Workout[]>([])
  const hasMore = ref(true)
  const offset = ref(0)
  const loading = ref(false)
  const programFilter = ref<number | null>(null)

  async function loadWorkouts(reset = false) {
    if (loading.value) return
    loading.value = true

    if (reset) {
      workouts.value = []
      offset.value = 0
      hasMore.value = true
    }

    try {
      const params = new URLSearchParams()
      params.set('limit', String(LIMIT))
      params.set('offset', String(offset.value))
      if (programFilter.value !== null) {
        params.set('program_id', String(programFilter.value))
      }

      const res = await apiFetch(`${API_BASE}?${params}`)
      if (!res.ok) throw new Error(`Failed to fetch workouts: ${res.statusText}`)
      const data = await res.json()
      const items: Workout[] = data.items

      workouts.value = reset ? items : [...workouts.value, ...items]
      hasMore.value = items.length === LIMIT
      offset.value += items.length
    } catch (e) {
      console.error('Failed to load workout history:', e)
    } finally {
      loading.value = false
    }
  }

  function setFilter(programId: number | null) {
    programFilter.value = programId
    loadWorkouts(true)
  }

  return {
    workouts,
    hasMore,
    offset,
    loading,
    programFilter,
    loadWorkouts,
    setFilter,
  }
})
