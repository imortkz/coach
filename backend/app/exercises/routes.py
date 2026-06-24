"""Exercise API routes — async MongoDB/Beanie."""

import re

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exercises.models import Exercise
from app.exercises.schemas import ExerciseCreate, ExerciseRead, ExerciseUpdate
from app.programs.service import list_current_programs
from app.workouts.schemas import (
    ExerciseHistoryResponse,
    ExerciseSession,
    ExerciseSessionSet,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _exercise_to_read(ex: Exercise) -> ExerciseRead:
    return ExerciseRead(
        id=ex.id,
        name=ex.name,
        muscle_group=ex.muscle_group,
        equipment=ex.equipment,
        is_custom=ex.is_custom,
        name_ru=ex.name_ru,
        gif_url=ex.gif_url,
    )


@router.get("/", response_model=list[ExerciseRead])
async def list_exercises(
    muscle_group: str | None = Query(None),
    equipment: str | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """List exercises: shared (seeded) + current user's custom exercises."""
    query: dict = {
        "$or": [
            {"user_id": None},
            {"user_id": current_user.id},
        ]
    }
    if muscle_group:
        query["muscle_group"] = muscle_group
    if equipment:
        query["equipment"] = equipment
    if search:
        query["name"] = {"$regex": re.escape(search), "$options": "i"}

    exercises = await Exercise.find(query).sort(
        [("muscle_group", 1), ("name", 1)]
    ).to_list()
    return [_exercise_to_read(ex) for ex in exercises]


@router.get("/{exercise_id}", response_model=ExerciseRead)
async def get_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a single exercise by ID (shared or owned by current user)."""
    exercise = await Exercise.get(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise.user_id is not None and exercise.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return _exercise_to_read(exercise)


@router.post("/", response_model=ExerciseRead, status_code=201)
async def create_exercise(
    data: ExerciseCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a custom exercise owned by the current user."""
    exercise = Exercise(
        user_id=current_user.id,
        name=data.name,
        muscle_group=data.muscle_group,
        equipment=data.equipment,
        is_custom=True,
    )
    await exercise.insert()
    return _exercise_to_read(exercise)


@router.put("/{exercise_id}", response_model=ExerciseRead)
async def update_exercise(
    exercise_id: str,
    data: ExerciseUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a custom exercise owned by the current user."""
    exercise = await Exercise.get(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if not exercise.is_custom:
        raise HTTPException(status_code=403, detail="Cannot modify a seeded exercise")
    if exercise.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot modify another user's exercise")

    if data.name is not None:
        exercise.name = data.name
    if data.muscle_group is not None:
        exercise.muscle_group = data.muscle_group
    if data.equipment is not None:
        exercise.equipment = data.equipment

    await exercise.save()
    return _exercise_to_read(exercise)


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a custom exercise owned by the current user."""
    exercise = await Exercise.get(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if not exercise.is_custom:
        raise HTTPException(status_code=403, detail="Cannot delete a seeded exercise")
    if exercise.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's exercise")

    # Check if exercise is used in the CURRENT version of any of the user's
    # programs. Historical versions are immutable and keep a denormalized copy
    # of the exercise, so only current usage should block deletion.
    current_programs = await list_current_programs(current_user.id)
    programs_using = [
        p for p in current_programs
        if any(pe.exercise_id == exercise_id for pe in p.exercises)
    ]
    if programs_using:
        program_names = [p.name for p in programs_using]
        raise HTTPException(
            status_code=409,
            detail=f"Exercise is used in programs: {', '.join(program_names)}",
        )

    await exercise.delete()


@router.get("/{exercise_id}/history", response_model=ExerciseHistoryResponse)
async def exercise_history(
    exercise_id: str,
    limit: int = Query(20),
    program_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Get per-exercise workout history with optional progression suggestion."""
    exercise = await Exercise.get(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    # Allow history for shared or owned exercises
    if exercise.user_id is not None and exercise.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Exercise not found")

    from app.workouts.models import Workout

    # Find completed workouts for current user containing sets for this exercise
    workouts = await Workout.find(
        {
            "user_id": current_user.id,
            "completed_at": {"$ne": None},
            "sets.exercise_id": exercise_id,
        }
    ).sort([("completed_at", -1)]).limit(limit).to_list()

    sessions: list[ExerciseSession] = []
    for w in workouts:
        exercise_sets = [s for s in w.sets if s.exercise_id == exercise_id]

        non_warmup = [s for s in exercise_sets if not s.is_warmup]
        best_weight = max(
            (s.weight_kg for s in non_warmup if s.weight_kg is not None),
            default=None,
        )
        total_volume = sum(
            (s.weight_kg or 0) * (s.reps or 0)
            for s in non_warmup
        )

        sessions.append(ExerciseSession(
            date=w.completed_at,
            sets=[
                ExerciseSessionSet(
                    set_number=s.set_number,
                    weight_kg=s.weight_kg,
                    reps=s.reps,
                    is_warmup=s.is_warmup,
                )
                for s in sorted(exercise_sets, key=lambda x: x.set_number)
            ],
            best_weight=best_weight,
            total_volume=total_volume,
        ))

    # Compute progression suggestion if program_id provided
    suggestion = None
    if program_id is not None:
        from app.workouts.routes import compute_progression
        suggestion = await compute_progression(exercise_id, program_id, current_user.id)

    return ExerciseHistoryResponse(sessions=sessions, suggestion=suggestion)
