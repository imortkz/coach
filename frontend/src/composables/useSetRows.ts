import type { PreFillSet, ProgramSet, WorkoutSet } from '@/types'

export interface SetRowData {
  setNumber: number
  loggedSet: WorkoutSet | null
  templateSet: ProgramSet | null
  preFillSet: PreFillSet | null
  isWarmup: boolean
  isExtra: boolean
  showRpe: boolean
}

export function buildSetRows({
  exerciseId,
  templateSets,
  loggedSets,
  preFillSets,
  extraSetNumbers,
  skippedTemplateSets,
}: {
  exerciseId: string
  templateSets: ProgramSet[]
  loggedSets: WorkoutSet[]
  preFillSets: PreFillSet[]
  extraSetNumbers: number[]
  skippedTemplateSets: Set<string>
}): SetRowData[] {
  const rows: SetRowData[] = []

  for (const templateSet of templateSets) {
    const loggedSet = loggedSets.find(
      (set) => set.set_number === templateSet.set_number && set.exercise_id === exerciseId,
    )
    if (!loggedSet && skippedTemplateSets.has(`${exerciseId}:${templateSet.set_number}`)) {
      continue
    }
    const preFillSet = preFillSets.find((set) => set.set_number === templateSet.set_number)
    rows.push({
      setNumber: templateSet.set_number,
      loggedSet: loggedSet ?? null,
      templateSet,
      preFillSet: preFillSet ?? null,
      isWarmup: templateSet.is_warmup,
      isExtra: false,
      showRpe: false,
    })
  }

  const templateNumbers = new Set(templateSets.map((set) => set.set_number))
  const loggedExtras = loggedSets
    .filter((set) => !templateNumbers.has(set.set_number))
    .sort((a, b) => a.set_number - b.set_number)

  for (const extra of loggedExtras) {
    rows.push({
      setNumber: extra.set_number,
      loggedSet: extra,
      templateSet: null,
      preFillSet: null,
      isWarmup: extra.is_warmup,
      isExtra: true,
      showRpe: false,
    })
  }

  const existingNumbers = new Set(rows.map((row) => row.setNumber))
  for (const setNumber of extraSetNumbers) {
    if (!existingNumbers.has(setNumber)) {
      rows.push({
        setNumber,
        loggedSet: null,
        templateSet: null,
        preFillSet: null,
        isWarmup: false,
        isExtra: true,
        showRpe: false,
      })
    }
  }

  const workingSetNumbers = rows
    .filter((row) => !row.isWarmup)
    .map((row) => row.setNumber)
    .sort((a, b) => a - b)
  const afterFirstWorking = new Set(workingSetNumbers.slice(1))
  for (const row of rows) {
    row.showRpe = !row.isWarmup && afterFirstWorking.has(row.setNumber)
  }

  return rows
}
