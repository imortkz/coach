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

function mountCard(workout: Workout) {
  setActivePinia(createPinia())
  return mount(WorkoutCard, {
    props: { workout, expanded: false, programName: 'Push Day' },
    global: { plugins: [makeI18n()] },
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
})
