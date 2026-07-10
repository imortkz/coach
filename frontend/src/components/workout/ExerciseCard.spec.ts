import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import ExerciseCard from '@/components/workout/ExerciseCard.vue'
import en from '@/locales/en'
import type { Exercise, ProgramSet, WorkoutSet } from '@/types'

function makeI18n() {
  return createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en } })
}

const BASE_EXERCISE: Exercise = {
  id: 'ex-1',
  name: 'Barbell Bench Press',
  muscle_group: 'Chest',
  equipment: 'Barbell',
  is_custom: false,
  name_ru: 'Жим штанги лёжа',
  gif_url: '/gifs/barbell-bench-press.gif',
}

function mountCard(exercise: Exercise, overrides: Partial<{
  loggedSets: WorkoutSet[]
  templateSets: ProgramSet[]
  extraSetNumbers: number[]
}> = {}) {
  return mount(ExerciseCard, {
    props: {
      exercise,
      loggedSets: [],
      templateSets: [],
      preFillSets: [],
      extraSetNumbers: [],
      ...overrides,
    },
    global: { plugins: [makeI18n()] },
  })
}

describe('ExerciseCard — demo gif on request during workout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders a how-to button when the exercise has a gif_url', () => {
    const wrapper = mountCard(BASE_EXERCISE)
    expect(wrapper.find('[data-testid="how-to-btn"]').exists()).toBe(true)
  })

  it('does NOT render the how-to button when gif_url is null', () => {
    const wrapper = mountCard({ ...BASE_EXERCISE, gif_url: null })
    expect(wrapper.find('[data-testid="how-to-btn"]').exists()).toBe(false)
  })

  it('is collapsed by default — no gif image shown until requested', () => {
    const wrapper = mountCard(BASE_EXERCISE)
    expect(wrapper.find('[data-testid="how-to-gif"]').exists()).toBe(false)
  })

  it('reveals the gif image with the correct src when the button is tapped', async () => {
    const wrapper = mountCard(BASE_EXERCISE)
    await wrapper.find('[data-testid="how-to-btn"]').trigger('click')
    const img = wrapper.find('[data-testid="how-to-gif"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('/gifs/barbell-bench-press.gif')
  })

  it('toggles the gif off on a second tap', async () => {
    const wrapper = mountCard(BASE_EXERCISE)
    const btn = wrapper.find('[data-testid="how-to-btn"]')
    await btn.trigger('click')
    expect(wrapper.find('[data-testid="how-to-gif"]').exists()).toBe(true)
    await btn.trigger('click')
    expect(wrapper.find('[data-testid="how-to-gif"]').exists()).toBe(false)
  })
})

describe('ExerciseCard — RPE prompt visibility', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const templateSets: ProgramSet[] = [
    { id: 'ts-1', program_exercise_id: 'pe-1', set_number: 1, target_reps: 10, target_weight_kg: 20, is_warmup: true },
    { id: 'ts-2', program_exercise_id: 'pe-1', set_number: 2, target_reps: 8, target_weight_kg: 40, is_warmup: false },
    { id: 'ts-3', program_exercise_id: 'pe-1', set_number: 3, target_reps: 8, target_weight_kg: 40, is_warmup: false },
  ]

  function loggedSet(setNumber: number, isWarmup: boolean): WorkoutSet {
    return {
      id: `ws-${setNumber}`,
      workout_id: 'w-1',
      exercise_id: 'ex-1',
      set_number: setNumber,
      weight_kg: 40,
      reps: 8,
      is_warmup: isWarmup,
      logged_at: '2026-07-10T00:00:00Z',
      rpe: null,
      rest_seconds: null,
    }
  }

  it('does not show the RPE prompt for a logged warmup set', () => {
    const wrapper = mountCard(BASE_EXERCISE, {
      templateSets,
      loggedSets: [loggedSet(1, true)],
    })
    expect(wrapper.findAll('[data-testid="rpe-picker"]')).toHaveLength(0)
  })

  it('does not show the RPE prompt for the first logged working set', () => {
    const wrapper = mountCard(BASE_EXERCISE, {
      templateSets,
      loggedSets: [loggedSet(1, true), loggedSet(2, false)],
    })
    expect(wrapper.findAll('[data-testid="rpe-picker"]')).toHaveLength(0)
  })

  it('shows the RPE prompt for the second logged working set', () => {
    const wrapper = mountCard(BASE_EXERCISE, {
      templateSets,
      loggedSets: [loggedSet(1, true), loggedSet(2, false), loggedSet(3, false)],
    })
    expect(wrapper.findAll('[data-testid="rpe-picker"]')).toHaveLength(1)
  })

  it('shows the RPE prompt for an extra working set logged beyond the plan', () => {
    const wrapper = mountCard(BASE_EXERCISE, {
      templateSets,
      loggedSets: [loggedSet(1, true), loggedSet(2, false), loggedSet(3, false), loggedSet(4, false)],
      extraSetNumbers: [4],
    })
    expect(wrapper.findAll('[data-testid="rpe-picker"]')).toHaveLength(2)
  })
})
