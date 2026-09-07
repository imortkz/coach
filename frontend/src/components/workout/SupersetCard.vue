<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useWorkoutsStore } from '@/stores/workouts'
import { useDisplayName } from '@/composables/useDisplayName'
import { buildSetRows, type SetRowData } from '@/composables/useSetRows'
import type { PreFillSet, ProgramExercise, WorkoutSet } from '@/types'
import SetRow from './SetRow.vue'

const props = defineProps<{
  members: ProgramExercise[]
  loggedSets: WorkoutSet[]
  preFill: Record<string, PreFillSet[]>
  extraSetNumbers: Array<{ exerciseId: string; setNumber: number }>
  skippedTemplateSets: Set<string>
}>()

const emit = defineEmits<{
  addSet: [exerciseId: string]
  setLogged: []
  deleteSet: [setId: string]
  removeExtra: [exerciseId: string, setNumber: number]
  removeExercise: []
  removeTemplate: [payload: { exerciseId: string; setNumber: number }]
}>()

const { t } = useI18n()
const { displayName } = useDisplayName()
const workoutsStore = useWorkoutsStore()

interface RoundItem {
  member: ProgramExercise
  row: SetRowData
}

const rowsByMember = computed(() => props.members.map((member) => ({
  member,
  rows: buildSetRows({
    exerciseId: member.exercise_id,
    templateSets: member.sets,
    loggedSets: props.loggedSets.filter((set) => set.exercise_id === member.exercise_id),
    preFillSets: props.preFill[member.exercise_id] ?? [],
    extraSetNumbers: props.extraSetNumbers
      .filter((extra) => extra.exerciseId === member.exercise_id)
      .map((extra) => extra.setNumber),
    skippedTemplateSets: props.skippedTemplateSets,
  }),
})))

const rounds = computed(() => {
  const roundNumbers = [...new Set(
    rowsByMember.value.flatMap(({ rows }) => rows.map((row) => row.setNumber)),
  )].sort((a, b) => a - b)
  return roundNumbers.map((roundNumber) => ({
    number: roundNumber,
    items: rowsByMember.value.flatMap<RoundItem>(({ member, rows }) => (
      rows.flatMap((row) => row.setNumber === roundNumber ? [{ member, row }] : [])
    )),
  }))
})

function suggestionSetNumber(member: ProgramExercise): number | null {
  if (!workoutsStore.suggestions[member.exercise_id]) return null
  const entry = rowsByMember.value.find((candidate) => candidate.member.exercise_id === member.exercise_id)
  return entry?.rows.find((row) => !row.isWarmup && !row.loggedSet)?.setNumber ?? null
}

async function handleComplete(
  payload: {
    exercise_id: string
    set_number: number
    weight_kg: number | null
    reps: number | null
    is_warmup: boolean
  },
  roundIndex: number,
) {
  try {
    await workoutsStore.logSet({
      ...payload,
      superset_group: props.members[0]?.superset_group ?? null,
    })
    const completedByThisLog = (item: RoundItem) => (
      item.member.exercise_id === payload.exercise_id && item.row.setNumber === payload.set_number
    )
    if (rounds.value[roundIndex].items.every((item) => item.row.loggedSet || completedByThisLog(item))) {
      emit('setLogged')
    }
  } catch {
    // error is set in store
  }
}

async function handleUpdate(payload: {
  setId: string
  weight_kg: number | null
  reps: number | null
  rpe: number | null
}) {
  try {
    await workoutsStore.updateSet(payload.setId, {
      weight_kg: payload.weight_kg,
      reps: payload.reps,
      rpe: payload.rpe,
    })
  } catch {
    // error is set in store
  }
}
</script>

<template>
  <div data-testid="superset-card" class="border-2 border-blue-200 rounded-xl overflow-hidden">
    <div class="px-4 py-3 bg-blue-50/70 border-b border-blue-100 flex items-center justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-blue-600">
          {{ t('programs.superset_label') }}
        </p>
        <p class="text-sm text-gray-600 mt-0.5">
          {{ members.map((member) => displayName(member.exercise!)).join(' · ') }}
        </p>
      </div>
      <button
        class="text-xs font-medium text-red-500 hover:text-red-700"
        :title="t('programs.remove_exercise_title')"
        @click="emit('removeExercise')"
      >
        {{ t('programs.delete') }}
      </button>
    </div>

    <div class="divide-y divide-blue-100">
      <section
        v-for="(round, roundIndex) in rounds"
        :key="round.number"
        :data-testid="`superset-round-${round.number}`"
        class="py-2"
      >
        <h3 class="px-4 pb-1 text-xs font-semibold text-blue-600">
          {{ t('workout.round_n', { n: round.number }) }}
        </h3>
        <div v-for="{ member, row } in round.items" :key="`${member.exercise_id}:${row.setNumber}`">
          <p class="px-4 pt-2 text-xs font-medium text-gray-700">
            {{ displayName(member.exercise!) }}
          </p>
          <SetRow
            :set-number="row.setNumber"
            :logged-set="row.loggedSet"
            :template-set="row.templateSet"
            :pre-fill-set="row.preFillSet"
            :is-warmup="row.isWarmup"
            :is-extra="row.isExtra"
            :exercise-id="member.exercise_id"
            :is-assisted="member.exercise?.is_assisted"
            :suggestion="workoutsStore.suggestions[member.exercise_id] ?? null"
            :show-suggestion="row.setNumber === suggestionSetNumber(member)"
            :show-rpe="row.showRpe"
            @complete="(payload) => handleComplete(payload, roundIndex)"
            @update="handleUpdate"
            @delete="emit('deleteSet', $event)"
            @remove-extra="emit('removeExtra', member.exercise_id, $event)"
            @remove-template="emit('removeTemplate', $event)"
          />
        </div>
      </section>
    </div>

    <div class="border-t border-blue-100 px-4 py-2 flex flex-wrap gap-x-4 gap-y-1">
      <button
        v-for="member in members"
        :key="member.exercise_id"
        class="text-xs text-blue-600 hover:text-blue-700 font-medium"
        @click="emit('addSet', member.exercise_id)"
      >
        + {{ t('programs.add_set') }} · {{ displayName(member.exercise!) }}
      </button>
    </div>
  </div>
</template>
