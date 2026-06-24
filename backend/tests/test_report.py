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
    async def test_report_week_boundary_and_none_reps(self, db, client, test_user):
        """A set on Sun 23:59 and one on the following Mon 00:00 land in
        different ISO weeks; a set with reps=None is excluded from volume."""
        now = datetime.now(timezone.utc)
        today = now.date()
        current_monday = today - timedelta(days=today.weekday())

        # Use two adjacent weeks that are inside a generous window.
        # last_monday is the start of the most recent full week before current.
        last_monday = current_monday - timedelta(days=7)
        prev_sunday_2359 = datetime.combine(
            last_monday - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
        ).replace(hour=23, minute=59)
        last_monday_0000 = datetime.combine(
            last_monday, datetime.min.time(), tzinfo=timezone.utc
        )

        # Sunday-night workout: counts a normal set + a None-reps set (excluded).
        sun = Workout(
            user_id=test_user.id,
            started_at=prev_sunday_2359,
            completed_at=prev_sunday_2359,
            sets=[
                _set(exercise_name="Bench Press", muscle_group="Chest", weight_kg=50.0, reps=10),
                _set(exercise_name="Bench Press", muscle_group="Chest", weight_kg=50.0, reps=None, set_number=2),
            ],
        )
        await sun.insert()

        # Monday-morning workout in the next ISO week.
        mon = Workout(
            user_id=test_user.id,
            started_at=last_monday_0000,
            completed_at=last_monday_0000,
            sets=[_set(exercise_name="Squat", muscle_group="Legs", weight_kg=80.0, reps=5)],
        )
        await mon.insert()

        resp = await client.get("/api/workouts/report?weeks=4")
        assert resp.status_code == 200
        data = resp.json()

        sun_label = _iso_week(prev_sunday_2359)
        mon_label = _iso_week(last_monday_0000)
        assert sun_label != mon_label  # adjacent days, different ISO weeks

        # Frequency: one workout in each of the two distinct weeks.
        freq = {e["week"]: e["count"] for e in data["frequency_by_week"]}
        assert freq.get(sun_label) == 1
        assert freq.get(mon_label) == 1

        # Volume in the Sunday week: only the reps-set counts (50*10=500),
        # the reps=None set is dropped — so it does NOT become 1000.
        sun_chest = sum(
            e["volume_kg"] for e in data["volume_by_week"]
            if e["week"] == sun_label and e["muscle_group"] == "Chest"
        )
        assert sun_chest == pytest.approx(500.0)

        # Volume in the Monday week landed under that week, not the Sunday week.
        mon_legs = sum(
            e["volume_kg"] for e in data["volume_by_week"]
            if e["week"] == mon_label and e["muscle_group"] == "Legs"
        )
        assert mon_legs == pytest.approx(400.0)

    @pytest.mark.asyncio
    async def test_report_rejects_invalid_weeks(self, client, db, test_user):
        resp = await client.get("/api/workouts/report?weeks=0")
        assert resp.status_code == 422
        resp = await client.get("/api/workouts/report?weeks=53")
        assert resp.status_code == 422
