import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'

import SessionTable from '@/components/history/SessionTable.vue'
import en from '@/locales/en'
import type { ExerciseSession, ExerciseSessionSet } from '@/types'

function makeI18n() {
  return createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en } })
}

function mountTable(set: ExerciseSessionSet) {
  const session: ExerciseSession = {
    date: '2026-07-01T10:30:00Z',
    sets: [set],
    best_weight: set.weight_kg,
    total_volume: (set.weight_kg ?? 0) * (set.reps ?? 0),
  }

  return mount(SessionTable, {
    props: { sessions: [session] },
    global: { plugins: [makeI18n()] },
  })
}

function makeSet(overrides: Partial<ExerciseSessionSet> = {}): ExerciseSessionSet {
  return {
    set_number: 2,
    weight_kg: 60,
    reps: 8,
    is_warmup: false,
    rpe: null,
    ...overrides,
  }
}

describe('SessionTable — per-set RPE', () => {
  it('renders a localized RPE label after reps when RPE is recorded', () => {
    const wrapper = mountTable(makeSet({ rpe: 8 }))

    expect(wrapper.text()).toContain('60kg x 8 · RPE 8')
  })

  it('does not render a separator or label when RPE is null', () => {
    const wrapper = mountTable(makeSet())

    expect(wrapper.text()).toContain('60kg x 8')
    expect(wrapper.text()).not.toContain('·')
    expect(wrapper.text()).not.toContain('RPE')
  })

  it('does not render RPE for a warm-up set even when one is stored', () => {
    const wrapper = mountTable(makeSet({ is_warmup: true, rpe: 9 }))

    expect(wrapper.text()).toContain('(W)')
    expect(wrapper.text()).toContain('60kg x 8')
    expect(wrapper.text()).not.toContain('·')
    expect(wrapper.text()).not.toContain('RPE')
  })

  it('renders a recorded numeric RPE even when its value is zero', () => {
    const wrapper = mountTable(makeSet({ rpe: 0 }))

    expect(wrapper.text()).toContain('60kg x 8 · RPE 0')
  })
})
