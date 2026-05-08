import { apiFetch } from '@/lib/apiFetch'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Workout, WorkoutSet, WorkoutStartResponse, PreFillSet, SuggestionInfo } from '@/types'

const API_BASE = '/api/workouts'

export const useWorkoutsStore = defineStore('workouts', () => {
  const activeWorkout = ref<Workout | null>(null)
  const preFill = ref<Record<string, PreFillSet[]>>({})
  const suggestions = ref<Record<string, SuggestionInfo>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchActiveWorkout(): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const res = await apiFetch(`${API_BASE}/active`)
      if (res.status === 404) {
        activeWorkout.value = null
        return false
      }
      if (!res.ok) throw new Error(`Failed to fetch active workout: ${res.statusText}`)
      activeWorkout.value = await res.json()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch active workout'
      activeWorkout.value = null
      return false
    } finally {
      loading.value = false
    }
  }

  async function startWorkout(programId: string): Promise<Workout> {
    loading.value = true
    error.value = null
    try {
      const res = await apiFetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ program_id: programId }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to start workout: ${res.statusText}`)
      }
      const data: WorkoutStartResponse = await res.json()
      activeWorkout.value = data
      preFill.value = data.pre_fill
      suggestions.value = data.suggestions || {}
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start workout'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function logSet(data: {
    exercise_id: string
    set_number: number
    weight_kg: number | null
    reps: number | null
    is_warmup: boolean
  }): Promise<WorkoutSet> {
    if (!activeWorkout.value) throw new Error('No active workout')
    error.value = null
    try {
      const res = await apiFetch(`${API_BASE}/${activeWorkout.value.id}/sets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to log set: ${res.statusText}`)
      }
      const createdSet: WorkoutSet = await res.json()
      activeWorkout.value.sets.push(createdSet)
      return createdSet
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to log set'
      throw e
    }
  }

  async function updateSet(
    setId: string,
    data: { weight_kg?: number | null; reps?: number | null }
  ): Promise<WorkoutSet> {
    if (!activeWorkout.value) throw new Error('No active workout')
    error.value = null
    try {
      const res = await apiFetch(`${API_BASE}/${activeWorkout.value.id}/sets/${setId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to update set: ${res.statusText}`)
      }
      const updatedSet: WorkoutSet = await res.json()
      const idx = activeWorkout.value.sets.findIndex((s) => s.id === setId)
      if (idx !== -1) {
        activeWorkout.value.sets[idx] = updatedSet
      }
      return updatedSet
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update set'
      throw e
    }
  }

  async function deleteSet(setId: string): Promise<void> {
    if (!activeWorkout.value) throw new Error('No active workout')
    error.value = null
    try {
      const res = await apiFetch(`${API_BASE}/${activeWorkout.value.id}/sets/${setId}`, {
        method: 'DELETE',
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to delete set: ${res.statusText}`)
      }
      activeWorkout.value.sets = activeWorkout.value.sets.filter((s) => s.id !== setId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete set'
      throw e
    }
  }

  async function deleteExerciseSets(exerciseId: string): Promise<void> {
    if (!activeWorkout.value) throw new Error('No active workout')
    error.value = null
    try {
      const res = await apiFetch(`${API_BASE}/${activeWorkout.value.id}/exercises/${exerciseId}`, {
        method: 'DELETE',
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to remove exercise: ${res.statusText}`)
      }
      activeWorkout.value.sets = activeWorkout.value.sets.filter((s) => s.exercise_id !== exerciseId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to remove exercise'
      throw e
    }
  }

  async function discardWorkout(): Promise<void> {
    if (!activeWorkout.value) throw new Error('No active workout')
    error.value = null
    try {
      const res = await apiFetch(`${API_BASE}/${activeWorkout.value.id}`, {
        method: 'DELETE',
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to discard workout: ${res.statusText}`)
      }
      activeWorkout.value = null
      preFill.value = {}
      suggestions.value = {}
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to discard workout'
      throw e
    }
  }

  async function fetchRestTimerSetting(): Promise<number> {
    try {
      const res = await apiFetch('/api/settings/rest_timer_seconds')
      if (res.status === 404) return 120
      if (!res.ok) return 120
      const data = await res.json()
      const parsed = parseInt(data.value, 10)
      return isNaN(parsed) ? 120 : parsed
    } catch {
      return 120
    }
  }

  async function completeWorkout(): Promise<Workout> {
    if (!activeWorkout.value) throw new Error('No active workout')
    error.value = null
    try {
      const res = await apiFetch(`${API_BASE}/${activeWorkout.value.id}/complete`, {
        method: 'PATCH',
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to complete workout: ${res.statusText}`)
      }
      const completed: Workout = await res.json()
      activeWorkout.value = completed
      return completed
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to complete workout'
      throw e
    }
  }

  return {
    activeWorkout,
    preFill,
    suggestions,
    loading,
    error,
    fetchActiveWorkout,
    startWorkout,
    logSet,
    updateSet,
    deleteSet,
    deleteExerciseSets,
    discardWorkout,
    fetchRestTimerSetting,
    completeWorkout,
  }
})
