export interface Exercise {
  id: string
  name: string
  muscle_group: string
  equipment: string
  is_custom: boolean
  name_ru?: string | null
  gif_url?: string | null
}

export interface ProgramSet {
  id: string
  program_exercise_id: string
  set_number: number
  target_reps: number
  target_weight_kg: number | null
  is_warmup: boolean
}

export interface Program {
  id: string
  name: string
  created_at: string
  rest_timer_disabled: boolean
  exercises: ProgramExercise[]
}

export interface ProgramExercise {
  id: string
  program_id: string
  exercise_id: string
  order: number
  sets: ProgramSet[]
  exercise?: Exercise
}

export interface Workout {
  id: string
  program_id: string | null
  started_at: string
  completed_at: string | null
  sets: WorkoutSet[]
}

export interface WorkoutSet {
  id: string
  workout_id: string
  exercise_id: string
  set_number: number
  weight_kg: number | null
  reps: number | null
  is_warmup: boolean
  exercise?: Exercise
}

export interface PreFillSet {
  set_number: number
  weight_kg: number | null
  reps: number | null
  is_warmup: boolean
}

export interface SuggestionInfo {
  type: 'weight' | 'reps' | 'keep'
  suggested_weight_kg: number | null
  suggested_reps: number | null
  increment: number | null
  reason: 'hit_target' | 'missed_reps'
}

export interface WorkoutStartResponse extends Workout {
  pre_fill: Record<string, PreFillSet[]>
  suggestions: Record<string, SuggestionInfo>
}

export interface ExerciseSessionSet {
  set_number: number
  weight_kg: number | null
  reps: number | null
  is_warmup: boolean
}

export interface ExerciseSession {
  date: string
  sets: ExerciseSessionSet[]
  best_weight: number | null
  total_volume: number
}

export interface ExerciseHistoryResponse {
  sessions: ExerciseSession[]
  suggestion: SuggestionInfo | null
}

export interface ReportVolumeEntry {
  week: string
  muscle_group: string
  volume_kg: number
}

export interface ReportFrequencyEntry {
  week: string
  count: number
}

export interface ReportPersonalRecord {
  exercise_name: string
  best_weight_in_period: number
  previous_best: number | null
  is_new_pr: boolean
}

export interface ReportResponse {
  weeks: string[]
  volume_by_week: ReportVolumeEntry[]
  frequency_by_week: ReportFrequencyEntry[]
  personal_records: ReportPersonalRecord[]
}
