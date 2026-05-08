import { apiFetch } from '@/lib/apiFetch'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Exercise } from '@/types'

const API_BASE = '/api/exercises'

export const useExercisesStore = defineStore('exercises', () => {
  const exercises = ref<Exercise[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchExercises(params?: {
    muscle_group?: string
    equipment?: string
    search?: string
  }) {
    loading.value = true
    error.value = null
    try {
      const query = new URLSearchParams()
      if (params?.muscle_group) query.set('muscle_group', params.muscle_group)
      if (params?.equipment) query.set('equipment', params.equipment)
      if (params?.search) query.set('search', params.search)

      const url = query.toString() ? `${API_BASE}?${query}` : API_BASE
      const res = await apiFetch(url)
      if (!res.ok) throw new Error(`Failed to fetch exercises: ${res.statusText}`)
      exercises.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch exercises'
      exercises.value = []
    } finally {
      loading.value = false
    }
  }

  async function createExercise(data: {
    name: string
    muscle_group: string
    equipment: string
  }): Promise<Exercise> {
    error.value = null
    const res = await apiFetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Failed to create exercise: ${res.statusText}`)
    }
    const created: Exercise = await res.json()
    await fetchExercises()
    return created
  }

  async function updateExercise(
    id: string,
    data: { name?: string; muscle_group?: string; equipment?: string },
  ): Promise<Exercise> {
    error.value = null
    const res = await apiFetch(`${API_BASE}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Failed to update exercise: ${res.statusText}`)
    }
    const updated: Exercise = await res.json()
    await fetchExercises()
    return updated
  }

  async function deleteExercise(id: string): Promise<void> {
    error.value = null
    const res = await apiFetch(`${API_BASE}/${id}`, { method: 'DELETE' })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      if (res.status === 409) {
        throw new Error(body.detail || 'Cannot delete: exercise is used in a program')
      }
      throw new Error(body.detail || `Failed to delete exercise: ${res.statusText}`)
    }
    await fetchExercises()
  }

  return { exercises, loading, error, fetchExercises, createExercise, updateExercise, deleteExercise }
})
