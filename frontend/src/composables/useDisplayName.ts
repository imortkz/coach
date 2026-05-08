import { useSettingsStore } from '@/stores/settings'
import type { Exercise } from '@/types'

export function useDisplayName() {
  const settingsStore = useSettingsStore()

  function displayName(exercise: Exercise): string {
    if (settingsStore.language === 'ru' && exercise.name_ru) {
      return exercise.name_ru
    }
    return exercise.name
  }

  return { displayName }
}
