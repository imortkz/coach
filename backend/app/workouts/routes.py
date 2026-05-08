"""Workout logging and settings API routes — async MongoDB/Beanie."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exercises.models import Exercise
from app.exercises.schemas import ExerciseRead
from app.programs.models import Program
from app.workouts.models import Setting, Workout, WorkoutSet
from app.workouts.schemas import (
    PreFillSet,
    ReportFrequencyEntry,
    ReportPersonalRecord,
    ReportResponse,
    ReportVolumeEntry,
    SettingRead,
    SettingUpdate,
    SuggestionInfo,
    WorkoutCreate,
    WorkoutListResponse,
    WorkoutRead,
    WorkoutSetCreate,
    WorkoutSetRead,
    WorkoutSetUpdate,
    WorkoutStartResponse,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])
settings_router = APIRouter(prefix="/settings", tags=["settings"])


def _set_to_read(ws: WorkoutSet, workout_id: str) -> WorkoutSetRead:
    """Convert an embedded WorkoutSet to WorkoutSetRead."""
    return WorkoutSetRead(
        id=ws.id,
        workout_id=workout_id,
        exercise_id=ws.exercise_id,
        set_number=ws.set_number,
        weight_kg=ws.weight_kg,
        reps=ws.reps,
        is_warmup=ws.is_warmup,
        exercise=ExerciseRead(
            id=ws.exercise_id,
            name=ws.exercise_name,
            muscle_group=ws.exercise_muscle_group,
            equipment=ws.exercise_equipment,
            is_custom=ws.exercise_is_custom,
        ),
    )


def _workout_to_read(w: Workout) -> WorkoutRead:
    """Convert a Workout document to WorkoutRead."""
    return WorkoutRead(
        id=w.id,
        program_id=w.program_id,
        started_at=w.started_at,
        completed_at=w.completed_at,
        sets=[_set_to_read(s, w.id) for s in w.sets],
    )


async def _compute_prefill(program_id: str, user_id: str) -> dict[str, list[PreFillSet]]:
    """Compute pre-fill data for a new workout."""
    program = await Program.get(program_id)
    if not program:
        return {}

    pre_fill: dict[str, list[PreFillSet]] = {}

    for pe in program.exercises:
        exercise_id = pe.exercise_id

        # Find the most recent completed workout by this user with sets for this exercise
        last_workout = await Workout.find_one(
            {
                "user_id": user_id,
                "completed_at": {"$ne": None},
                "sets.exercise_id": exercise_id,
            },
            sort=[("completed_at", -1)],
        )

        if last_workout:
            last_sets = sorted(
                [s for s in last_workout.sets if s.exercise_id == exercise_id],
                key=lambda s: s.set_number,
            )
            pre_fill[exercise_id] = [
                PreFillSet(
                    set_number=ws.set_number,
                    weight_kg=ws.weight_kg,
                    reps=ws.reps,
                    is_warmup=ws.is_warmup,
                )
                for ws in last_sets
            ]
        else:
            # Fall back to program template targets
            pre_fill[exercise_id] = [
                PreFillSet(
                    set_number=ps.set_number,
                    weight_kg=ps.target_weight_kg,
                    reps=ps.target_reps,
                    is_warmup=ps.is_warmup,
                )
                for ps in sorted(pe.sets, key=lambda s: s.set_number)
            ]

    return pre_fill


# --- Equipment increment defaults (kg) ---
EQUIPMENT_INCREMENTS: dict[str, float | None] = {
    "Barbell": 2.5,
    "Dumbbell": 2.0,
    "Cable": 2.5,
    "Machine": 2.5,
    "Bodyweight": None,
    "Kettlebell": 4.0,
    "Smith Machine": 2.5,
    "EZ Bar": 2.5,
    "Resistance Band": None,
    "Trap Bar": 2.5,
    "Landmine": 2.5,
}


async def compute_progression(
    exercise_id: str,
    program_id: str,
    user_id: str | None = None,
) -> SuggestionInfo | None:
    """Compute progression suggestion for an exercise."""
    exercise = await Exercise.get(exercise_id)
    if not exercise:
        return None

    program = await Program.get(program_id)
    if not program:
        return None

    # Find the ProgramExercise
    pe = next((e for e in program.exercises if e.exercise_id == exercise_id), None)
    if not pe:
        return None

    # Get target reps from non-warmup sets
    non_warmup_program_sets = [s for s in pe.sets if not s.is_warmup]
    if not non_warmup_program_sets:
        return None
    target_reps = non_warmup_program_sets[0].target_reps

    # Build query — filter by user_id if provided
    workout_query: dict = {
        "completed_at": {"$ne": None},
        "sets.exercise_id": exercise_id,
    }
    if user_id:
        workout_query["user_id"] = user_id

    # Find last completed workout with sets for this exercise
    last_workout = await Workout.find_one(
        workout_query,
        sort=[("completed_at", -1)],
    )
    if not last_workout:
        return None

    # Get non-warmup sets from last session
    non_warmup_sets = [
        s for s in last_workout.sets
        if s.exercise_id == exercise_id and not s.is_warmup
    ]
    if not non_warmup_sets:
        return None

    # Check if all non-warmup sets are at the same weight
    weights = {ws.weight_kg for ws in non_warmup_sets}
    if len(weights) > 1:
        return None  # Mixed weights

    current_weight = non_warmup_sets[0].weight_kg

    # Check if all sets hit target reps
    all_hit_target = all(
        ws.reps is not None and ws.reps >= target_reps
        for ws in non_warmup_sets
    )

    # Get equipment increment (check user override first)
    equipment = exercise.equipment
    settings_key = f"progression_increment_{equipment.lower().replace(' ', '_')}"
    setting_query = {"key": settings_key}
    if user_id:
        setting_query["user_id"] = user_id
    setting = await Setting.find_one(setting_query)
    if setting:
        increment = float(setting.value)
    else:
        increment = EQUIPMENT_INCREMENTS.get(equipment)

    if all_hit_target:
        if increment is None:
            return SuggestionInfo(
                type="reps",
                suggested_weight_kg=current_weight,
                suggested_reps=target_reps + 1,
                increment=None,
                reason="hit_target",
            )
        else:
            new_weight = (current_weight or 0) + increment
            return SuggestionInfo(
                type="weight",
                suggested_weight_kg=new_weight,
                suggested_reps=None,
                increment=increment,
                reason="hit_target",
            )
    else:
        return SuggestionInfo(
            type="keep",
            suggested_weight_kg=current_weight,
            suggested_reps=None,
            increment=None,
            reason="missed_reps",
        )


@router.get("", response_model=WorkoutListResponse)
async def list_workouts(
    limit: int = 20,
    offset: int = 0,
    program_id: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """List completed workouts in reverse chronological order with pagination."""
    if limit > 100:
        limit = 100

    query: dict = {
        "user_id": current_user.id,
        "completed_at": {"$ne": None},
    }
    if program_id is not None:
        query["program_id"] = program_id

    workouts = await Workout.find(query).sort(
        [("completed_at", -1)]
    ).skip(offset).limit(limit).to_list()

    return WorkoutListResponse(items=[_workout_to_read(w) for w in workouts])


@router.post("", response_model=WorkoutStartResponse, status_code=201)
async def start_workout(
    data: WorkoutCreate,
    current_user: User = Depends(get_current_user),
):
    """Start a new workout from a program template with pre-fill data."""
    program = await Program.get(data.program_id)
    if not program or program.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Program not found")

    workout = Workout(
        user_id=current_user.id,
        program_id=data.program_id,
        program_version=program.current_version,
    )
    await workout.insert()

    pre_fill = await _compute_prefill(data.program_id, current_user.id)

    # Compute progression suggestions for each exercise
    suggestions: dict[str, SuggestionInfo] = {}
    for pe in program.exercises:
        suggestion = await compute_progression(pe.exercise_id, data.program_id, current_user.id)
        if suggestion is not None:
            suggestions[pe.exercise_id] = suggestion

    return WorkoutStartResponse(
        id=workout.id,
        program_id=workout.program_id,
        started_at=workout.started_at,
        completed_at=workout.completed_at,
        sets=[],
        pre_fill=pre_fill,
        suggestions=suggestions,
    )


@router.get("/active", response_model=WorkoutRead)
async def get_active_workout(
    current_user: User = Depends(get_current_user),
):
    """Get the current in-progress workout (completed_at IS NULL)."""
    workout = await Workout.find_one(
        {"user_id": current_user.id, "completed_at": None},
        sort=[("started_at", -1)],
    )
    if not workout:
        raise HTTPException(status_code=404, detail="No active workout")
    return _workout_to_read(workout)


def _iso_week_label(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


# NB: must be registered BEFORE /{workout_id} or FastAPI will route /report
# into get_workout(workout_id="report") and 404. Same reason /active sits
# above the param route.
@router.get("/report", response_model=ReportResponse)
async def get_progress_report(
    weeks: int = 4,
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Aggregate progress over the last `weeks` calendar weeks (Mon–Sun).

    Volume is sum of (weight_kg * reps) for non-warmup sets, grouped by
    ISO week label and muscle group. Frequency counts distinct completed
    workouts per week. Personal records compare each exercise's heaviest
    non-warmup set in the period to its prior best across all earlier
    workouts of the user.
    """
    if weeks < 1 or weeks > 52:
        raise HTTPException(status_code=422, detail="weeks must be between 1 and 52")

    now = datetime.now(timezone.utc)
    today = now.date()
    current_monday = today - timedelta(days=today.weekday())
    start_monday = current_monday - timedelta(days=7 * (weeks - 1))
    start_dt = datetime.combine(start_monday, datetime.min.time(), tzinfo=timezone.utc)

    week_starts = [start_monday + timedelta(days=7 * i) for i in range(weeks)]
    week_labels = [
        _iso_week_label(datetime.combine(ws, datetime.min.time(), tzinfo=timezone.utc))
        for ws in week_starts
    ]

    def label_for(dt: datetime) -> str | None:
        d = dt.date()
        for i, ws in enumerate(week_starts):
            if ws <= d < ws + timedelta(days=7):
                return week_labels[i]
        return None

    workouts_in_period = await Workout.find(
        {
            "user_id": current_user.id,
            "completed_at": {"$ne": None, "$gte": start_dt},
        }
    ).to_list()

    volume_acc: dict[tuple[str, str], float] = defaultdict(float)
    freq_acc: dict[str, int] = defaultdict(int)
    counted_workouts: set[tuple[str, str]] = set()
    pr_in_period: dict[str, float] = {}

    for w in workouts_in_period:
        if w.completed_at is None:
            continue
        wk_label = label_for(w.completed_at)
        if wk_label is None:
            continue

        if (wk_label, w.id) not in counted_workouts:
            counted_workouts.add((wk_label, w.id))
            freq_acc[wk_label] += 1

        for s in w.sets:
            if s.is_warmup or s.weight_kg is None or s.reps is None:
                continue
            volume_acc[(wk_label, s.exercise_muscle_group or "Other")] += s.weight_kg * s.reps

            curr_best = pr_in_period.get(s.exercise_name, 0.0)
            if s.weight_kg > curr_best:
                pr_in_period[s.exercise_name] = s.weight_kg

    prior_workouts = await Workout.find(
        {
            "user_id": current_user.id,
            "completed_at": {"$ne": None, "$lt": start_dt},
        }
    ).to_list()

    prior_best: dict[str, float] = {}
    for w in prior_workouts:
        for s in w.sets:
            if s.is_warmup or s.weight_kg is None:
                continue
            if s.weight_kg > prior_best.get(s.exercise_name, 0.0):
                prior_best[s.exercise_name] = s.weight_kg

    personal_records = sorted(
        (
            ReportPersonalRecord(
                exercise_name=name,
                best_weight_in_period=period_max,
                previous_best=prior_best.get(name),
                is_new_pr=(name not in prior_best) or (period_max > prior_best[name]),
            )
            for name, period_max in pr_in_period.items()
        ),
        key=lambda r: r.exercise_name,
    )

    volume_by_week = [
        ReportVolumeEntry(week=wl, muscle_group=mg, volume_kg=vol)
        for (wl, mg), vol in sorted(volume_acc.items())
    ]
    frequency_by_week = [
        ReportFrequencyEntry(week=wl, count=freq_acc.get(wl, 0))
        for wl in week_labels
    ]

    return ReportResponse(
        weeks=week_labels,
        volume_by_week=volume_by_week,
        frequency_by_week=frequency_by_week,
        personal_records=personal_records,
    )


@router.get("/{workout_id}", response_model=WorkoutRead)
async def get_workout(
    workout_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a single workout owned by the current user."""
    workout = await Workout.get(workout_id)
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workout not found")
    return _workout_to_read(workout)


@router.patch("/{workout_id}/complete", response_model=WorkoutRead)
async def complete_workout(
    workout_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a workout as completed."""
    workout = await Workout.get(workout_id)
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workout not found")

    workout.completed_at = datetime.now(timezone.utc)
    await workout.save()
    return _workout_to_read(workout)


@router.post("/{workout_id}/sets", response_model=WorkoutSetRead, status_code=201)
async def log_set(
    workout_id: str,
    data: WorkoutSetCreate,
    current_user: User = Depends(get_current_user),
):
    """Log a new set in a workout."""
    workout = await Workout.get(workout_id)
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Resolve exercise details for denormalization
    exercise = await Exercise.get(data.exercise_id)

    workout_set = WorkoutSet(
        exercise_id=data.exercise_id,
        exercise_name=exercise.name if exercise else "",
        exercise_muscle_group=exercise.muscle_group if exercise else "",
        exercise_equipment=exercise.equipment if exercise else "",
        exercise_is_custom=exercise.is_custom if exercise else False,
        set_number=data.set_number,
        weight_kg=data.weight_kg,
        reps=data.reps,
        is_warmup=data.is_warmup,
    )
    workout.sets.append(workout_set)
    await workout.save()

    return _set_to_read(workout_set, workout.id)


@router.put("/{workout_id}/sets/{set_id}", response_model=WorkoutSetRead)
async def update_set(
    workout_id: str,
    set_id: str,
    data: WorkoutSetUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update weight and/or reps on a logged set."""
    workout = await Workout.get(workout_id)
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workout not found")

    target_set = next((s for s in workout.sets if s.id == set_id), None)
    if not target_set:
        raise HTTPException(status_code=404, detail="Set not found")

    if data.weight_kg is not None:
        target_set.weight_kg = data.weight_kg
    if data.reps is not None:
        target_set.reps = data.reps

    await workout.save()
    return _set_to_read(target_set, workout.id)


@router.delete("/{workout_id}/sets/{set_id}", status_code=204)
async def delete_set(
    workout_id: str,
    set_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a single set from a workout."""
    workout = await Workout.get(workout_id)
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workout not found")

    original_len = len(workout.sets)
    workout.sets = [s for s in workout.sets if s.id != set_id]
    if len(workout.sets) == original_len:
        raise HTTPException(status_code=404, detail="Set not found")

    await workout.save()
    return Response(status_code=204)


@router.delete("/{workout_id}/exercises/{exercise_id}", status_code=204)
async def delete_exercise_sets(
    workout_id: str,
    exercise_id: str,
    current_user: User = Depends(get_current_user),
):
    """Remove all sets for a given exercise from a workout."""
    workout = await Workout.get(workout_id)
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workout not found")

    workout.sets = [s for s in workout.sets if s.exercise_id != exercise_id]
    await workout.save()
    return Response(status_code=204)


@router.delete("/{workout_id}", status_code=204)
async def discard_workout(
    workout_id: str,
    current_user: User = Depends(get_current_user),
):
    """Discard (delete) an entire workout and its sets."""
    workout = await Workout.get(workout_id)
    if not workout or workout.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workout not found")

    await workout.delete()
    return Response(status_code=204)


# --- Settings ---


@settings_router.get("/{key}", response_model=SettingRead)
async def get_setting(
    key: str,
    current_user: User = Depends(get_current_user),
):
    """Get a setting by key for the current user."""
    setting = await Setting.find_one({"user_id": current_user.id, "key": key})
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SettingRead(key=setting.key, value=setting.value)


@settings_router.put("/{key}", response_model=SettingRead)
async def upsert_setting(
    key: str,
    data: SettingUpdate,
    current_user: User = Depends(get_current_user),
):
    """Create or update a setting for the current user."""
    setting = await Setting.find_one({"user_id": current_user.id, "key": key})
    if setting:
        setting.value = data.value
        await setting.save()
    else:
        setting = Setting(user_id=current_user.id, key=key, value=data.value)
        await setting.insert()

    return SettingRead(key=setting.key, value=setting.value)
