"""Tests for the M005 progress-report endpoint."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from app.workouts.models import Workout, WorkoutSet


def _iso_week(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _set(
    *,
    exercise_id: str = "ex-1",
    exercise_name: str = "Bench Press",
    muscle_group: str = "Chest",
    set_number: int = 1,
    weight_kg: float | None = 60.0,
    reps: int | None = 10,
    is_warmup: bool = False,
) -> WorkoutSet:
    return WorkoutSet(
        exercise_id=exercise_id,
        exercise_name=exercise_name,
        exercise_muscle_group=muscle_group,
        exercise_equipment="Barbell",
        set_number=set_number,
        weight_kg=weight_kg,
        reps=reps,
        is_warmup=is_warmup,
    )


@pytest_asyncio.fixture
async def history_with_pr(db, test_user):
    """Build a 4-week period that exercises every part of the report shape.

    Layout (monday-anchored, relative to "today"):
      - prior_workout: 50 days ago — Bench 70kg (the all-time pre-period best)
      - week-3 (3 weeks before current): Bench 80kg + warmup, Squat 100kg
      - week-1 (1 week before current): Bench 85kg (new PR vs 80, vs prior 70)
      - week-0 (current week): Squat 110kg
    """
    now = datetime.now(timezone.utc)
    today = now.date()
    current_monday_date = today - timedelta(days=today.weekday())

    def at(weeks_back: int, hour: int = 12) -> datetime:
        d = current_monday_date - timedelta(days=7 * weeks_back)
        return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).replace(hour=hour)

    prior = Workout(
        user_id=test_user.id,
        started_at=now - timedelta(days=50),
        completed_at=now - timedelta(days=50),
        sets=[_set(exercise_name="Bench Press", muscle_group="Chest", weight_kg=70.0, reps=5)],
    )
    await prior.insert()

    w_minus3 = Workout(
        user_id=test_user.id,
        started_at=at(3),
        completed_at=at(3),
        sets=[
            _set(exercise_name="Bench Press", muscle_group="Chest", weight_kg=40.0, reps=10, is_warmup=True),
            _set(exercise_name="Bench Press", muscle_group="Chest", weight_kg=80.0, reps=5, set_number=2),
            _set(exercise_name="Squat", muscle_group="Legs", weight_kg=100.0, reps=5, set_number=3),
        ],
    )
    await w_minus3.insert()

    w_minus1 = Workout(
        user_id=test_user.id,
        started_at=at(1),
        completed_at=at(1),
        sets=[_set(exercise_name="Bench Press", muscle_group="Chest", weight_kg=85.0, reps=3)],
    )
    await w_minus1.insert()

    w_now = Workout(
        user_id=test_user.id,
        started_at=at(0),
        completed_at=at(0),
        sets=[_set(exercise_name="Squat", muscle_group="Legs", weight_kg=110.0, reps=3)],
    )
    await w_now.insert()

    return {"prior": prior, "w_minus3": w_minus3, "w_minus1": w_minus1, "w_now": w_now}


class TestProgressReport:
    @pytest.mark.asyncio
    async def test_report_typical_user(self, client, history_with_pr):
        resp = await client.get("/api/workouts/report?weeks=4")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["weeks"]) == 4
        assert all(w.startswith(("20", "19")) and "-W" in w for w in data["weeks"])

        freq_by_label = {entry["week"]: entry["count"] for entry in data["frequency_by_week"]}
        assert sum(freq_by_label.values()) == 3  # three workouts in period
        assert len(freq_by_label) == 4  # zero-filled even for empty weeks

        # Volume: warmup excluded, only working sets counted.
        # w_minus3: Bench 80*5 = 400 (Chest), Squat 100*5 = 500 (Legs)
        # w_minus1: Bench 85*3 = 255 (Chest)
        # w_now:    Squat 110*3 = 330 (Legs)
        # Total Chest in period = 655, Total Legs = 830.
        chest_total = sum(e["volume_kg"] for e in data["volume_by_week"] if e["muscle_group"] == "Chest")
        legs_total = sum(e["volume_kg"] for e in data["volume_by_week"] if e["muscle_group"] == "Legs")
        assert chest_total == pytest.approx(655.0)
        assert legs_total == pytest.approx(830.0)

        prs = {p["exercise_name"]: p for p in data["personal_records"]}
        assert set(prs.keys()) == {"Bench Press", "Squat"}

        bench = prs["Bench Press"]
        assert bench["best_weight_in_period"] == pytest.approx(85.0)
        assert bench["previous_best"] == pytest.approx(70.0)  # the prior workout 50d ago
        assert bench["is_new_pr"] is True

        squat = prs["Squat"]
        assert squat["best_weight_in_period"] == pytest.approx(110.0)
        assert squat["previous_best"] is None  # no prior squat history before period
        assert squat["is_new_pr"] is True

    @pytest.mark.asyncio
    async def test_report_empty_period(self, db, client, test_user):
        # Single workout 60 days ago, well outside any plausible window of 4 weeks.
        long_ago = datetime.now(timezone.utc) - timedelta(days=60)
        old = Workout(
            user_id=test_user.id,
            started_at=long_ago,
            completed_at=long_ago,
            sets=[_set(weight_kg=60.0, reps=8)],
        )
        await old.insert()

        resp = await client.get("/api/workouts/report?weeks=4")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["weeks"]) == 4
        assert data["volume_by_week"] == []
        assert data["personal_records"] == []
        # Frequency must be zero-filled for every week in the range
        assert len(data["frequency_by_week"]) == 4
        assert all(entry["count"] == 0 for entry in data["frequency_by_week"])

    @pytest.mark.asyncio
    async def test_prior_set_without_reps_does_not_set_previous_best(self, db, client, test_user):
        # Arrange: a prior-period set logged with a weight but no reps (reps=None)
        # at 100kg, and a real in-period working set at 80kg for the same exercise.
        # A reps=None set is incomplete and must never count toward PR history,
        # exactly as it is excluded from the in-period best.
        now = datetime.now(timezone.utc)
        today = now.date()
        current_monday_date = today - timedelta(days=today.weekday())
        in_period_dt = datetime.combine(
            current_monday_date, datetime.min.time(), tzinfo=timezone.utc
        ).replace(hour=12)

        prior = Workout(
            user_id=test_user.id,
            started_at=now - timedelta(days=50),
            completed_at=now - timedelta(days=50),
            sets=[_set(exercise_name="Deadlift", muscle_group="Back", weight_kg=100.0, reps=None)],
        )
        await prior.insert()

        in_period = Workout(
            user_id=test_user.id,
            started_at=in_period_dt,
            completed_at=in_period_dt,
            sets=[_set(exercise_name="Deadlift", muscle_group="Back", weight_kg=80.0, reps=5)],
        )
        await in_period.insert()

        # Act
        resp = await client.get("/api/workouts/report?weeks=4")

        # Assert
        assert resp.status_code == 200
        prs = {p["exercise_name"]: p for p in resp.json()["personal_records"]}
        assert "Deadlift" in prs
        deadlift = prs["Deadlift"]
        assert deadlift["best_weight_in_period"] == pytest.approx(80.0)
        # The phantom 100kg reps=None prior set must NOT mask the real record.
        assert deadlift["previous_best"] is None
        assert deadlift["is_new_pr"] is True

    @pytest.mark.asyncio
    async def test_report_rejects_invalid_weeks(self, client, db, test_user):
        resp = await client.get("/api/workouts/report?weeks=0")
        assert resp.status_code == 422
        resp = await client.get("/api/workouts/report?weeks=53")
        assert resp.status_code == 422
