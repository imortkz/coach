import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import WorkoutCard from '@/components/history/WorkoutCard.vue'
import en from '@/locales/en'
import type { Workout } from '@/types'

function makeI18n() {
  return createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en } })
}

function baseWorkout(overrides: Partial<Workout> = {}): Workout {
  return {
    id: 'w-1',
    program_id: 'p-1',
    program_version: 2,
    started_at: '2026-07-01T10:00:00Z',
    completed_at: '2026-07-01T10:30:00Z',
    sets: [],
    ...overrides,
  }
}

function mountCard(workout: Workout, expanded = false) {
  setActivePinia(createPinia())
  return mount(WorkoutCard, {
    props: { workout, expanded, programName: 'Push Day' },
    global: {
      plugins: [makeI18n()],
      stubs: { RouterLink: { template: '<a><slot /></a>' } },
    },
  })
}

describe('WorkoutCard — program version badge (M010)', () => {
  it('shows a "vN" badge when the workout carries program_version', () => {
    const wrapper = mountCard(baseWorkout({ program_version: 3 }))
    expect(wrapper.text()).toContain('v3')
  })

  it('does not render a badge when program_version is null (legacy workout)', () => {
    const wrapper = mountCard(baseWorkout({ program_version: null }))
    expect(wrapper.find('[data-testid="version-badge"]').exists()).toBe(false)
  })

  it('emits view-version with programId and version when the badge is clicked', async () => {
    const wrapper = mountCard(baseWorkout({ program_id: 'p-42', program_version: 5 }))
    const badge = wrapper.find('[data-testid="version-badge"]')
    expect(badge.exists()).toBe(true)

    await badge.trigger('click')

    const emitted = wrapper.emitted('view-version')
    expect(emitted).toBeTruthy()
    expect(emitted![0]).toEqual(['p-42', 5])
  })

  it('groups superset exercises under one localized label', () => {
    const wrapper = mountCard(baseWorkout({
      sets: [
        {
          id: 's-1', workout_id: 'w-1', exercise_id: 'bench', superset_group: 'group-1',
          set_number: 1, weight_kg: 60, reps: 8, is_warmup: false,
          logged_at: '2026-07-01T10:01:00Z', rpe: null, rest_seconds: null,
          exercise: { id: 'bench', name: 'Bench', muscle_group: 'Chest', equipment: 'Barbell' },
        },
        {
          id: 's-2', workout_id: 'w-1', exercise_id: 'row', superset_group: 'group-1',
          set_number: 1, weight_kg: 60, reps: 8, is_warmup: false,
          logged_at: '2026-07-01T10:02:00Z', rpe: null, rest_seconds: 60,
          exercise: { id: 'row', name: 'Row', muscle_group: 'Back', equipment: 'Barbell' },
        },
        {
          id: 's-3', workout_id: 'w-1', exercise_id: 'squat', superset_group: null,
          set_number: 1, weight_kg: 100, reps: 5, is_warmup: false,
          logged_at: '2026-07-01T10:03:00Z', rpe: null, rest_seconds: 60,
          exercise: { id: 'squat', name: 'Squat', muscle_group: 'Legs', equipment: 'Barbell' },
        },
      ],
    }), true)

    expect(wrapper.findAll('[data-testid="history-superset"]')).toHaveLength(1)
    expect(wrapper.find('[data-testid="history-superset"]').text()).toContain('Superset')
    expect(wrapper.find('[data-testid="history-superset"]').text()).toContain('Bench')
    expect(wrapper.find('[data-testid="history-superset"]').text()).toContain('Row')
    expect(wrapper.findAll('[data-testid="history-exercise"]')).toHaveLength(1)
  })
})
