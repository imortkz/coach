import { describe, expect, it, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { createRouter, createMemoryHistory, type Router } from 'vue-router'

import ProgramEditView from '@/views/ProgramEditView.vue'
import { useProgramsStore } from '@/stores/programs'
import { useExercisesStore } from '@/stores/exercises'
import en from '@/locales/en'

// A real, well-formed UUID — the exact shape that broke prod (#20) when an
// older version coerced route.params.id via Number() into NaN, producing a
// request to /api/programs/NaN.
const PROGRAM_UUID = '3f2504e0-4f89-41d3-9a0c-0305e82c3301'

function makeRouter(): Router {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/programs', name: 'programs', component: { template: '<div />' } },
      { path: '/programs/new', name: 'program-new', component: ProgramEditView },
      { path: '/programs/:id/edit', name: 'program-edit', component: ProgramEditView },
    ],
  })
}

function makeI18n() {
  return createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en } })
}

async function mountAtEditRoute(uuid: string) {
  const router = makeRouter()
  const i18n = makeI18n()
  router.push(`/programs/${uuid}/edit`)
  await router.isReady()

  const wrapper = mount(ProgramEditView, {
    global: { plugins: [router, i18n] },
  })
  return wrapper
}

describe('ProgramEditView — UUID id is kept as a string (issue #20)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('fetches the program with the raw UUID string, never NaN or a number', async () => {
    // Stub the store boundary actions so nothing hits the network and we can
    // observe the argument the component hands to the store.
    const programsStore = useProgramsStore()
    const exercisesStore = useExercisesStore()
    const fetchProgram = vi
      .spyOn(programsStore, 'fetchProgram')
      .mockResolvedValue({ id: PROGRAM_UUID, name: 'Push Day', exercises: [] } as never)
    vi.spyOn(exercisesStore, 'fetchExercises').mockResolvedValue(undefined as never)

    await mountAtEditRoute(PROGRAM_UUID)
    await flushPromises()

    expect(fetchProgram).toHaveBeenCalledTimes(1)
    const passedId = fetchProgram.mock.calls[0][0]
    expect(passedId).toBe(PROGRAM_UUID)
    expect(typeof passedId).toBe('string')
    expect(Number.isNaN(passedId as unknown as number)).toBe(false)
  })

  it('updates the program with the raw UUID string when the form is saved', async () => {
    const programsStore = useProgramsStore()
    const exercisesStore = useExercisesStore()
    vi.spyOn(programsStore, 'fetchProgram').mockResolvedValue({
      id: PROGRAM_UUID,
      name: 'Push Day',
      exercises: [],
    } as never)
    vi.spyOn(exercisesStore, 'fetchExercises').mockResolvedValue(undefined as never)
    const updateProgram = vi.spyOn(programsStore, 'updateProgram').mockResolvedValue({} as never)

    const wrapper = await mountAtEditRoute(PROGRAM_UUID)
    await flushPromises()

    // Provide a minimal valid form: a name + one exercise with its default sets.
    const programName = wrapper.find('input[type="text"]')
    await programName.setValue('Renamed Program')

    // Add one exercise straight through the public UI path. The picker reads
    // from the exercises store, so seed it.
    exercisesStore.exercises = [
      {
        id: '11111111-1111-1111-1111-111111111111',
        name: 'Bench Press',
        muscle_group: 'chest',
        equipment: 'barbell',
        is_custom: false,
        name_ru: null,
        gif_url: null,
      },
    ] as never
    const addExerciseBtn = wrapper.findAll('button').find((b) => b.text().includes('Add Exercise'))
    expect(addExerciseBtn).toBeDefined()
    await addExerciseBtn!.trigger('click') // open picker
    await flushPromises()
    // Click the exercise option in the picker list.
    const optionButtons = wrapper.findAll('button').filter((b) => b.text().includes('Bench Press'))
    await optionButtons[optionButtons.length - 1].trigger('click')
    await flushPromises()

    // Save (the action button reads "Save Program").
    const saveButton = wrapper.findAll('button').find((b) => b.text() === 'Save Program')
    expect(saveButton).toBeDefined()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(updateProgram).toHaveBeenCalledTimes(1)
    const passedId = updateProgram.mock.calls[0][0]
    expect(passedId).toBe(PROGRAM_UUID)
    expect(typeof passedId).toBe('string')
  })
})
