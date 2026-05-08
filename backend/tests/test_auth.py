"""Tests for authentication endpoints and auth dependency."""

import pytest
import pytest_asyncio

from app.auth.models import User
from app.auth.jwt import create_access_token
from app.config import DEV_MODE, DEV_USER_ID


class TestDevMode:
    @pytest.mark.asyncio
    async def test_dev_login_endpoint(self, client, db):
        """Dev-login returns a token for the dev user (or existing test user at same ID)."""
        resp = await client.post("/api/auth/dev-login")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == DEV_USER_ID

    @pytest.mark.asyncio
    async def test_dev_mode_bypass_no_token(self, client, db):
        """No token + DEV_MODE=true => auto-auth as dev user."""
        resp = await client.get("/api/exercises")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_me_endpoint_dev_mode(self, client, db):
        """GET /api/auth/me returns dev user info in dev mode."""
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == DEV_USER_ID

    @pytest.mark.asyncio
    async def test_jwt_auth_valid_token(self, client, db):
        """Valid JWT token is accepted and resolves to the right user."""
        user = await User.find_one(User.id == DEV_USER_ID)
        token = create_access_token(user.id, user.telegram_id)

        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == DEV_USER_ID

    @pytest.mark.asyncio
    async def test_jwt_auth_invalid_token_returns_401(self, client, db):
        """Invalid JWT token returns 401."""
        resp = await client.get(
            "/api/exercises",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_jwt_auth_malformed_token_returns_401(self, client, db):
        """Malformed Authorization header returns 401."""
        resp = await client.get(
            "/api/exercises",
            headers={"Authorization": "Bearer not-a-jwt"},
        )
        assert resp.status_code == 401


class TestUserIsolation:
    @pytest_asyncio.fixture
    async def user_b(self, db) -> User:
        """Create a second user for isolation testing."""
        user = User(
            telegram_id=99999,
            username="userb",
            first_name="User B",
        )
        await user.insert()
        return user

    @pytest.mark.asyncio
    async def test_user_b_cannot_see_user_a_programs(self, client, db, test_user, user_b):
        """Programs created by user A are not visible to user B."""
        from app.programs.models import Program

        # Create program as user A (via API — dev mode)
        ex_resp = await client.post("/api/exercises", json={
            "name": "Test Ex",
            "muscle_group": "Chest",
            "equipment": "Barbell",
        })
        ex_id = ex_resp.json()["id"]

        prog_resp = await client.post("/api/programs", json={
            "name": "User A Program",
            "exercises": [
                {
                    "exercise_id": ex_id,
                    "order": 1,
                    "sets": [{"set_number": 1, "target_reps": 8, "target_weight_kg": 60.0}],
                }
            ],
        })
        assert prog_resp.status_code == 201
        program_id = prog_resp.json()["id"]

        # User B cannot list or get user A's program
        token_b = create_access_token(user_b.id, user_b.telegram_id)
        resp = await client.get("/api/programs", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert program_id not in ids

        resp = await client.get(f"/api/programs/{program_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_user_b_cannot_access_user_a_workout(self, client, db, test_user, user_b):
        """Workouts are scoped to their owner."""
        from app.programs.models import Program
        from app.workouts.models import Workout

        # Create workout as user A
        program = Program(user_id=test_user.id, name="A's Program", exercises=[])
        await program.insert()

        workout = Workout(user_id=test_user.id, program_id=program.id)
        await workout.insert()

        # User B cannot access it
        token_b = create_access_token(user_b.id, user_b.telegram_id)
        resp = await client.get(
            f"/api/workouts/{workout.id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404


class TestTelegramLogin:
    @pytest.mark.asyncio
    async def test_telegram_login_no_bot_token_returns_503(self, client, db, monkeypatch):
        """Without a bot token, Telegram login returns 503."""
        import app.auth.routes as auth_routes
        monkeypatch.setattr(auth_routes, "TELEGRAM_BOT_TOKEN", "")

        resp = await client.post("/api/auth/telegram", json={
            "id": 123456,
            "first_name": "John",
            "auth_date": 1700000000,
            "hash": "fakehash",
        })
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_telegram_login_invalid_hash_returns_401(self, client, db, monkeypatch):
        """Wrong HMAC hash returns 401."""
        import app.auth.routes as auth_routes
        monkeypatch.setattr(auth_routes, "TELEGRAM_BOT_TOKEN", "real_bot_token_123")

        resp = await client.post("/api/auth/telegram", json={
            "id": 123456,
            "first_name": "John",
            "auth_date": 1700000000,
            "hash": "invalidhash",
        })
        assert resp.status_code == 401
