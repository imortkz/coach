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
  id: number
  program_exercise_id: number
  set_number: number
  target_reps: number
  target_weight_kg: number | null
  is_warmup: boolean
}

export interface Program {
  id: number
  name: string
  created_at: string
  rest_timer_disabled: boolean
  exercises: ProgramExercise[]
}

export interface ProgramExercise {
  id: number
  program_id: number
  exercise_id: number
  order: number
  sets: ProgramSet[]
  exercise?: Exercise
}

export interface Workout {
  id: number
  program_id: number | null
  started_at: string
  completed_at: string | null
  sets: WorkoutSet[]
}

export interface WorkoutSet {
  id: number
  workout_id: number
  exercise_id: number
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
  pre_fill: Record<number, PreFillSet[]>
  suggestions: Record<number, SuggestionInfo>
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
