"""Lineage-aware resolution helpers for versioned program rows.

Every read of a program goes through here so call sites never accidentally
look a lineage up by Mongo ``_id`` (which no longer equals the program id) or
resolve "current" with an ad-hoc ``max()`` at read time.
"""

from app.programs.models import Program


async def get_current_program(program_id: str) -> Program | None:
    """Resolve the CURRENT row of a lineage (the highest version)."""
    return (
        await Program.find(Program.program_id == program_id)
        .sort([("version", -1)])
        .first_or_none()
    )


async def get_program_version(program_id: str, version: int) -> Program | None:
    """Resolve a specific historical row of a lineage by its pinned version."""
    return await Program.find_one(
        Program.program_id == program_id,
        Program.version == version,
    )


async def list_current_programs(user_id: str) -> list[Program]:
    """Return only the latest row per lineage for a user.

    A naive ``find({user_id})`` now returns every version of every program; at
    pet scale we fetch the user's rows sorted by (program_id, version desc) and
    reduce in Python, keeping the first (highest-version) row per lineage.
    """
    rows = (
        await Program.find(Program.user_id == user_id)
        .sort([("program_id", 1), ("version", -1)])
        .to_list()
    )
    latest: dict[str, Program] = {}
    for row in rows:
        if row.program_id not in latest:
            latest[row.program_id] = row
    return list(latest.values())
