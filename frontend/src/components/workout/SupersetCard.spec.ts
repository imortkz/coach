import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import SupersetCard from '@/components/workout/SupersetCard.vue'
import SetRow from '@/components/workout/SetRow.vue'
import { useWorkoutsStore } from '@/stores/workouts'
import en from '@/locales/en'
import type { ProgramExercise, WorkoutSet } from '@/types'

function member(id: string, name: string): ProgramExercise {
  return {
    id: `pe-${id}`,
    program_id: 'program-1',
    exercise_id: id,
    superset_group: 'group-1',
    order: id === 'bench' ? 1 : 2,
    exercise: {
      id,
      name,
      muscle_group: id === 'bench' ? 'Chest' : 'Back',
      equipment: 'Barbell',
      is_custom: false,
    },
    sets: [
      { set_number: 1, target_reps: 8, target_weight_kg: 60, is_warmup: false },
      { set_number: 2, target_reps: 8, target_weight_kg: 60, is_warmup: false },
    ],
  }
}

function logged(exerciseId: string): WorkoutSet {
  return {
    id: `set-${exerciseId}`,
    workout_id: 'workout-1',
    exercise_id: exerciseId,
    superset_group: 'group-1',
    set_number: 1,
    weight_kg: 60,
    reps: 8,
    is_warmup: false,
    logged_at: '2026-09-07T10:00:00Z',
    rpe: null,
    rest_seconds: null,
  }
}

describe('SupersetCard', () => {
  it('renders rounds and emits setLogged only after the final member of a round', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useWorkoutsStore()
    const logSet = vi.spyOn(store, 'logSet').mockResolvedValue(logged('bench'))
    const wrapper = mount(SupersetCard, {
      props: {
        members: [member('bench', 'Bench'), member('row', 'Row')],
        loggedSets: [],
        preFill: {},
        extraSetNumbers: [],
        skippedTemplateSets: new Set<string>(),
      },
      global: {
        plugins: [
          pinia,
          createI18n({ legacy: false, locale: 'en', messages: { en } }),
        ],
      },
    })

    expect(wrapper.findAll('[data-testid^="superset-round-"]')).toHaveLength(2)
    expect(wrapper.find('[data-testid="superset-round-1"]').findAllComponents(SetRow)).toHaveLength(2)

    const firstRow = wrapper.findAllComponents(SetRow).find(
      (row) => row.props('exerciseId') === 'bench' && row.props('setNumber') === 1,
    )!
    firstRow.vm.$emit('complete', {
      exercise_id: 'bench', set_number: 1, weight_kg: 60, reps: 8, is_warmup: false,
    })
    await flushPromises()
    expect(wrapper.emitted('setLogged')).toBeUndefined()
    expect(logSet.mock.calls[0][0].superset_group).toBe('group-1')

    await wrapper.setProps({ loggedSets: [logged('bench')] })
    const finalRow = wrapper.findAllComponents(SetRow).find(
      (row) => row.props('exerciseId') === 'row' && row.props('setNumber') === 1,
    )!
    finalRow.vm.$emit('complete', {
      exercise_id: 'row', set_number: 1, weight_kg: 60, reps: 8, is_warmup: false,
    })
    await flushPromises()
    expect(wrapper.emitted('setLogged')).toHaveLength(1)
  })
})
