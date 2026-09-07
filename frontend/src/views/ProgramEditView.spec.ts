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

async function mountAtNewRoute() {
  const router = makeRouter()
  router.push('/programs/new')
  await router.isReady()
  return mount(ProgramEditView, {
    global: { plugins: [router, makeI18n()] },
  })
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

  it('deletes an entire superset without deleting an unrelated exercise', async () => {
    const programsStore = useProgramsStore()
    const exercisesStore = useExercisesStore()
    vi.spyOn(exercisesStore, 'fetchExercises').mockResolvedValue(undefined as never)
    vi.spyOn(programsStore, 'fetchProgram').mockResolvedValue({
      id: PROGRAM_UUID,
      name: 'Superset Day',
      exercises: [
        {
          exercise_id: 'bench',
          order: 1,
          superset_group: 'group-1',
          exercise: { id: 'bench', name: 'Bench', muscle_group: 'Chest', equipment: 'Barbell' },
          sets: [{ set_number: 1, target_reps: 8, target_weight_kg: 60, is_warmup: false }],
        },
        {
          exercise_id: 'row',
          order: 2,
          superset_group: 'group-1',
          exercise: { id: 'row', name: 'Row', muscle_group: 'Back', equipment: 'Barbell' },
          sets: [{ set_number: 1, target_reps: 8, target_weight_kg: 60, is_warmup: false }],
        },
        {
          exercise_id: 'squat',
          order: 3,
          superset_group: null,
          exercise: { id: 'squat', name: 'Squat', muscle_group: 'Legs', equipment: 'Barbell' },
          sets: [{ set_number: 1, target_reps: 5, target_weight_kg: 100, is_warmup: false }],
        },
      ],
    } as never)
    const updateProgram = vi.spyOn(programsStore, 'updateProgram').mockResolvedValue({} as never)

    const wrapper = await mountAtEditRoute(PROGRAM_UUID)
    await flushPromises()
    expect(wrapper.findAll('[data-testid="superset-block"]')).toHaveLength(1)

    const deleteButton = wrapper
      .find('[data-testid="superset-block"]')
      .findAll('button')
      .find((button) => button.text() === 'Delete')
    await deleteButton!.trigger('click')
    await wrapper.findAll('button').find((button) => button.text() === 'Save Program')!.trigger('click')
    await flushPromises()

    const payload = updateProgram.mock.calls[0][1]
    expect(payload.exercises).toHaveLength(1)
    expect(payload.exercises[0].exercise_id).toBe('squat')
    expect(payload.exercises[0].superset_group).toBeNull()
  })

  it('creates a superset with one shared opaque group and equal set counts', async () => {
    const programsStore = useProgramsStore()
    const exercisesStore = useExercisesStore()
    exercisesStore.exercises = [
      {
        id: 'bench', name: 'Bench', muscle_group: 'Chest', equipment: 'Barbell',
        is_custom: false, name_ru: null, gif_url: null,
      },
      {
        id: 'row', name: 'Row', muscle_group: 'Back', equipment: 'Barbell',
        is_custom: false, name_ru: null, gif_url: null,
      },
    ] as never
    vi.spyOn(exercisesStore, 'fetchExercises').mockResolvedValue(undefined as never)
    const createProgram = vi.spyOn(programsStore, 'createProgram').mockResolvedValue({} as never)

    const wrapper = await mountAtNewRoute()
    await wrapper.findAll('button').find((button) => button.text().includes('Superset'))!.trigger('click')
    await wrapper.findAll('button').find((button) => button.text().includes('Bench'))!.trigger('click')
    await wrapper.findAll('button').find((button) => button.text().includes('Row'))!.trigger('click')
    await wrapper.find('[data-testid="confirm-superset"]').trigger('click')
    expect(wrapper.findAll('[data-testid="superset-block"]')).toHaveLength(1)

    await wrapper.find('input[type="text"]').setValue('Superset Day')
    await wrapper.findAll('button').find((button) => button.text() === 'Save Program')!.trigger('click')
    await flushPromises()

    const exercises = createProgram.mock.calls[0][0].exercises
    expect(exercises).toHaveLength(2)
    expect(exercises[0].superset_group).toBeTruthy()
    expect(exercises[1].superset_group).toBe(exercises[0].superset_group)
    expect(exercises[0].sets).toHaveLength(exercises[1].sets.length)
  })
})
