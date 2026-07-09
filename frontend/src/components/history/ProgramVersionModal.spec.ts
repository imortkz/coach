import { describe, expect, it, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import ProgramVersionModal from '@/components/history/ProgramVersionModal.vue'
import { useProgramsStore } from '@/stores/programs'
import en from '@/locales/en'
import type { ProgramVersionSnapshot } from '@/types'

function makeI18n() {
  return createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en } })
}

const SNAPSHOT: ProgramVersionSnapshot = {
  version: 1,
  is_current: false,
  name: 'День 1',
  rest_timer_disabled: false,
  exercises: [
    {
      exercise_id: 'ex-1',
      order: 1,
      exercise: {
        id: 'ex-1',
        name: 'Bench Press',
        muscle_group: 'Chest',
        equipment: 'Barbell',
        is_custom: false,
      },
      sets: [
        { set_number: 1, target_reps: 8, target_weight_kg: 60, is_warmup: false },
        { set_number: 2, target_reps: 8, target_weight_kg: 60, is_warmup: false },
      ],
    },
  ],
} as unknown as ProgramVersionSnapshot

describe('ProgramVersionModal — read-only version snapshot (M010)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('fetches the snapshot for the given program+version on mount and renders it', async () => {
    const store = useProgramsStore()
    const fetchProgramVersion = vi.spyOn(store, 'fetchProgramVersion').mockResolvedValue(SNAPSHOT)

    const wrapper = mount(ProgramVersionModal, {
      props: { programId: 'p-1', version: 1 },
      global: { plugins: [makeI18n()] },
    })
    await flushPromises()

    expect(fetchProgramVersion).toHaveBeenCalledWith('p-1', 1)
    expect(wrapper.text()).toContain('День 1')
    expect(wrapper.text()).toContain('Bench Press')
    expect(wrapper.text()).toContain('60')
  })

  it('shows an error state when the fetch fails', async () => {
    const store = useProgramsStore()
    vi.spyOn(store, 'fetchProgramVersion').mockRejectedValue(new Error('boom'))

    const wrapper = mount(ProgramVersionModal, {
      props: { programId: 'p-1', version: 1 },
      global: { plugins: [makeI18n()] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain(en.history.version_failed)
  })

  it('emits close when the close button is clicked', async () => {
    const store = useProgramsStore()
    vi.spyOn(store, 'fetchProgramVersion').mockResolvedValue(SNAPSHOT)

    const wrapper = mount(ProgramVersionModal, {
      props: { programId: 'p-1', version: 1 },
      global: { plugins: [makeI18n()] },
    })
    await flushPromises()

    await wrapper.find('[data-testid="version-modal-close"]').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
