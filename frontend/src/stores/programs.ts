import { apiFetch } from '@/lib/apiFetch'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Program } from '@/types'

const API_BASE = '/api/programs'

export interface ProgramCreatePayload {
  name: string
  rest_timer_disabled?: boolean
  exercises: {
    exercise_id: string
    order: number
    sets: {
      set_number: number
      target_reps: number
      target_weight_kg: number | null
      is_warmup: boolean
    }[]
  }[]
}

export const useProgramsStore = defineStore('programs', () => {
  const programs = ref<Program[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPrograms() {
    loading.value = true
    error.value = null
    try {
      const res = await apiFetch(API_BASE)
      if (!res.ok) throw new Error(`Failed to fetch programs: ${res.statusText}`)
      programs.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch programs'
      programs.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchProgram(id: string): Promise<Program> {
    const res = await apiFetch(`${API_BASE}/${id}`)
    if (!res.ok) throw new Error(`Failed to fetch program: ${res.statusText}`)
    return await res.json()
  }

  async function createProgram(data: ProgramCreatePayload): Promise<Program> {
    error.value = null
    const res = await apiFetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Failed to create program: ${res.statusText}`)
    }
    const created: Program = await res.json()
    await fetchPrograms()
    return created
  }

  async function updateProgram(id: string, data: ProgramCreatePayload): Promise<Program> {
    error.value = null
    const res = await apiFetch(`${API_BASE}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Failed to update program: ${res.statusText}`)
    }
    const updated: Program = await res.json()
    await fetchPrograms()
    return updated
  }

  async function deleteProgram(id: string): Promise<void> {
    error.value = null
    const res = await apiFetch(`${API_BASE}/${id}`, { method: 'DELETE' })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Failed to delete program: ${res.statusText}`)
    }
    await fetchPrograms()
  }

  return { programs, loading, error, fetchPrograms, fetchProgram, createProgram, updateProgram, deleteProgram }
})
