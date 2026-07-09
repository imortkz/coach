import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import ExerciseCard from '@/components/workout/ExerciseCard.vue'
import en from '@/locales/en'
import type { Exercise } from '@/types'

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

function mountCard(exercise: Exercise) {
  return mount(ExerciseCard, {
    props: {
      exercise,
      loggedSets: [],
      templateSets: [],
      preFillSets: [],
      extraSetNumbers: [],
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
