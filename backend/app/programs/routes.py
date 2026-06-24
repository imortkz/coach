"""Program CRUD API routes — versioned rows (current = max version)."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exercises.models import Exercise
from app.exercises.schemas import ExerciseRead
from app.programs.models import Program, ProgramExercise, ProgramSet
from app.programs.schemas import (
    ProgramCreate,
    ProgramExerciseRead,
    ProgramRead,
    ProgramSetRead,
    ProgramUpdate,
)
from app.programs.service import get_current_program, list_current_programs

router = APIRouter(prefix="/programs", tags=["programs"])


async def _resolve_exercises(exercises_data: list) -> list[ProgramExercise]:
    """Build ProgramExercise embedded docs, resolving exercise details."""
    result = []
    for ex_data in exercises_data:
        exercise = await Exercise.get(ex_data.exercise_id)
        result.append(ProgramExercise(
            exercise_id=ex_data.exercise_id,
            exercise_name=exercise.name if exercise else "",
            exercise_muscle_group=exercise.muscle_group if exercise else "",
            exercise_equipment=exercise.equipment if exercise else "",
            order=ex_data.order,
            sets=[
                ProgramSet(
                    set_number=s.set_number,
                    target_reps=s.target_reps,
                    target_weight_kg=s.target_weight_kg,
                    is_warmup=s.is_warmup,
                )
                for s in ex_data.sets
            ],
        ))
    return result


async def _program_to_read(program: Program) -> ProgramRead:
    """Convert a Program document to ProgramRead schema with exercise details."""
    exercises_read = []
    for pe in program.exercises:
        # Denormalized fallback — used only when the master Exercise has
        # been deleted. The embedded copy carries only the English fields,
        # so name_ru / gif_url are unavailable in this branch.
        exercise_read = ExerciseRead(
            id=pe.exercise_id,
            name=pe.exercise_name,
            muscle_group=pe.exercise_muscle_group,
            equipment=pe.exercise_equipment,
            is_custom=False,  # Denormalized; actual value doesn't matter for read
        )
        # Prefer the live Exercise so name_ru and gif_url follow the
        # master copy. Without these two fields the frontend's
        # displayName() always falls through to the English `name`
        # because name_ru is null on the response — that was the visible
        # bug in the program editor.
        ex = await Exercise.get(pe.exercise_id)
        if ex:
            exercise_read = ExerciseRead(
                id=ex.id,
                name=ex.name,
                muscle_group=ex.muscle_group,
                equipment=ex.equipment,
                is_custom=ex.is_custom,
                name_ru=ex.name_ru,
                gif_url=ex.gif_url,
            )

        exercises_read.append(ProgramExerciseRead(
            exercise_id=pe.exercise_id,
            order=pe.order,
            sets=[
                ProgramSetRead(
                    set_number=s.set_number,
                    target_reps=s.target_reps,
                    target_weight_kg=s.target_weight_kg,
                    is_warmup=s.is_warmup,
                )
                for s in pe.sets
            ],
            exercise=exercise_read,
        ))

    return ProgramRead(
        # Callers address a program by its LINEAGE id, never the per-row _id.
        id=program.program_id,
        name=program.name,
        created_at=program.created_at,
        rest_timer_disabled=program.rest_timer_disabled,
        current_version=program.version,
        exercises=exercises_read,
    )


@router.get("/", response_model=list[ProgramRead])
async def list_programs(
    current_user: User = Depends(get_current_user),
):
    """List the current row of each of the user's program lineages."""
    programs = await list_current_programs(current_user.id)
    programs.sort(key=lambda p: p.created_at, reverse=True)
    return [await _program_to_read(p) for p in programs]


@router.get("/{program_id}", response_model=ProgramRead)
async def get_program(
    program_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the current version of a single program owned by the current user."""
    program = await get_current_program(program_id)
    if not program or program.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Program not found")
    return await _program_to_read(program)


@router.post("/", response_model=ProgramRead, status_code=201)
async def create_program(
    data: ProgramCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a program with nested exercises and per-set targets."""
    exercises = await _resolve_exercises(data.exercises)

    program = Program(
        user_id=current_user.id,
        name=data.name,
        rest_timer_disabled=data.rest_timer_disabled,
        exercises=exercises,
        version=1,
    )
    await program.insert()
    return await _program_to_read(program)


@router.put("/{program_id}", response_model=ProgramRead)
async def update_program(
    program_id: str,
    data: ProgramUpdate,
    current_user: User = Depends(get_current_user),
):
    """Full-replace update via versioning: insert a NEW row at version+1.

    The previous row is left untouched as immutable history; "current" is
    simply the new highest version. The unique (user_id, program_id, version)
    index means a racing concurrent edit raises DuplicateKeyError rather than
    creating two rows at the same version.
    """
    current = await get_current_program(program_id)
    if not current or current.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Program not found")

    new_row = Program(
        program_id=current.program_id,
        version=current.version + 1,
        user_id=current.user_id,
        name=data.name,
        rest_timer_disabled=data.rest_timer_disabled,
        # Preserve the lineage's original creation time across edits so the
        # program's displayed created_at (and list ordering) stays stable.
        created_at=current.created_at,
        exercises=await _resolve_exercises(data.exercises),
    )
    await new_row.insert()
    return await _program_to_read(new_row)


@router.delete("/{program_id}", status_code=204)
async def delete_program(
    program_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a program owned by the current user — the WHOLE lineage.

    Deleting a single row would let max(version) resurrect a stale older
    version, so every version of the lineage is removed.
    """
    result = await Program.find(
        Program.program_id == program_id,
        Program.user_id == current_user.id,
    ).delete()
    if not result or result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Program not found")
