import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import UndoToast from '@/components/workout/UndoToast.vue'

// Smoke test for the test harness itself: proves vitest + jsdom + the `@`
// alias + the vue SFC plugin all work end to end. Real component behavior
// tests land in a follow-up slice.
describe('test harness smoke', () => {
  it('runs assertions', () => {
    expect(true).toBe(true)
  })

  it('mounts a .vue SFC resolved via the @ alias and renders its props', () => {
    const wrapper = mount(UndoToast, {
      props: { message: 'Set deleted', visible: true },
    })

    expect(wrapper.text()).toContain('Set deleted')
  })

  it('emits undo when the action is triggered', async () => {
    const wrapper = mount(UndoToast, {
      props: { message: 'Set deleted', visible: true },
    })

    await wrapper.get('button').trigger('click')

    expect(wrapper.emitted('undo')).toHaveLength(1)
  })
})
