"""Program CRUD API routes — async MongoDB/Beanie with versioning."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exercises.models import Exercise
from app.exercises.schemas import ExerciseRead
from app.programs.models import Program, ProgramExercise, ProgramSet, ProgramVersion
from app.programs.schemas import (
    ProgramCreate,
    ProgramExerciseRead,
    ProgramRead,
    ProgramSetRead,
    ProgramUpdate,
    ProgramVersionRead,
)

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


async def _exercises_to_read(exercises: list[ProgramExercise]) -> list[ProgramExerciseRead]:
    """Resolve embedded ProgramExercise docs to ProgramExerciseRead, joining the
    live Exercise catalog for name_ru/gif_url where the exercise still exists."""
    exercises_read = []
    for pe in exercises:
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

    return exercises_read


async def _program_to_read(program: Program) -> ProgramRead:
    """Convert a Program document to ProgramRead schema with exercise details."""
    return ProgramRead(
        id=program.id,
        name=program.name,
        created_at=program.created_at,
        rest_timer_disabled=program.rest_timer_disabled,
        current_version=program.current_version,
        exercises=await _exercises_to_read(program.exercises),
    )


@router.get("/", response_model=list[ProgramRead])
async def list_programs(
    current_user: User = Depends(get_current_user),
):
    """List all programs for the current user."""
    programs = await Program.find(
        {"user_id": current_user.id}
    ).sort([("created_at", -1)]).to_list()
    return [await _program_to_read(p) for p in programs]


@router.get("/{program_id}", response_model=ProgramRead)
async def get_program(
    program_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a single program owned by the current user."""
    program = await Program.get(program_id)
    if not program or program.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Program not found")
    return await _program_to_read(program)


@router.get("/{program_id}/versions/{version}", response_model=ProgramVersionRead)
async def get_program_version(
    program_id: str,
    version: int,
    current_user: User = Depends(get_current_user),
):
    """Read-only snapshot of how a program looked at a given version.

    `current_version` is served from the live program row; older versions come
    from the `versions[]` archive written on each edit (see update_program).
    """
    program = await Program.get(program_id)
    if not program or program.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Program not found")

    if version == program.current_version:
        return ProgramVersionRead(
            version=version,
            is_current=True,
            name=program.name,
            rest_timer_disabled=program.rest_timer_disabled,
            exercises=await _exercises_to_read(program.exercises),
        )

    snapshot = next((v for v in program.versions if v.version == version), None)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Program version not found")

    return ProgramVersionRead(
        version=version,
        is_current=False,
        name=snapshot.name,
        rest_timer_disabled=snapshot.rest_timer_disabled,
        exercises=await _exercises_to_read(snapshot.exercises),
    )


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
        current_version=1,
    )
    await program.insert()
    return await _program_to_read(program)


@router.put("/{program_id}", response_model=ProgramRead)
async def update_program(
    program_id: str,
    data: ProgramUpdate,
    current_user: User = Depends(get_current_user),
):
    """Full-replace update with versioning: archives current state before overwriting."""
    program = await Program.get(program_id)
    if not program or program.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Program not found")

    # Archive current version before modifying
    version_snapshot = ProgramVersion(
        version=program.current_version,
        name=program.name,
        rest_timer_disabled=program.rest_timer_disabled,
        exercises=program.exercises,
    )
    program.versions.append(version_snapshot)

    # Apply update
    program.name = data.name
    program.rest_timer_disabled = data.rest_timer_disabled
    program.exercises = await _resolve_exercises(data.exercises)
    program.current_version += 1
    program.version = program.current_version  # keep lineage field in sync

    await program.save()
    return await _program_to_read(program)


@router.delete("/{program_id}", status_code=204)
async def delete_program(
    program_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a program owned by the current user."""
    program = await Program.get(program_id)
    if not program or program.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Program not found")
    await program.delete()
