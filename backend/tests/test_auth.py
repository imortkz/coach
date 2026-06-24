"""Tests for authentication endpoints and auth dependency."""

import hashlib
import hmac

import pytest
import pytest_asyncio

from app.auth.models import User
from app.auth.jwt import create_access_token
from app.auth.telegram import verify_telegram_auth
from app.config import DEV_MODE, DEV_USER_ID


def sign_telegram_payload(bot_token: str, **fields: object) -> dict:
    """Build a Telegram login payload with a genuine HMAC hash.

    Signs exactly the fields passed, mirroring how the widget signs the
    data it sends. Returns the fields plus a valid ``hash``.
    """
    check_string = "\n".join(sorted(f"{k}={v}" for k, v in fields.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    digest = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return {**fields, "hash": digest}


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


class TestAgentToken:
    """The static agent service token authenticates as the configured user."""

    AGENT_TG_ID = 555000111
    AGENT_TOKEN = "agent-secret-token-for-tests"

    @pytest_asyncio.fixture
    async def agent_user(self, db) -> User:
        """User the agent token maps to (matched by telegram_id)."""
        user = User(
            telegram_id=self.AGENT_TG_ID,
            username="agent_owner",
            first_name="Agent Owner",
        )
        await user.insert()
        return user

    def _configure(self, monkeypatch):
        import app.auth.dependencies as deps
        monkeypatch.setattr(deps, "AGENT_API_TOKEN", self.AGENT_TOKEN)
        monkeypatch.setattr(deps, "AGENT_USER_TELEGRAM_ID", self.AGENT_TG_ID)

    @pytest.mark.asyncio
    async def test_agent_token_resolves_to_configured_user(
        self, client, db, agent_user, monkeypatch
    ):
        """Valid agent token authenticates as the configured user."""
        self._configure(monkeypatch)
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {self.AGENT_TOKEN}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == agent_user.id

    @pytest.mark.asyncio
    async def test_agent_token_has_write_access(
        self, client, db, agent_user, monkeypatch
    ):
        """Agent token can write (POST), i.e. full read+write as the user."""
        self._configure(monkeypatch)
        resp = await client.post(
            "/api/exercises",
            json={"name": "Agent Ex", "muscle_group": "Back", "equipment": "Barbell"},
            headers={"Authorization": f"Bearer {self.AGENT_TOKEN}"},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_wrong_agent_token_falls_through_to_jwt_and_401(
        self, client, db, agent_user, monkeypatch
    ):
        """A token that is neither the agent key nor a valid JWT returns 401."""
        self._configure(monkeypatch)
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not-the-agent-token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_agent_token_disabled_when_unconfigured(
        self, client, db, agent_user, monkeypatch
    ):
        """With AGENT_API_TOKEN empty the path is inert (token treated as bad JWT)."""
        import app.auth.dependencies as deps
        monkeypatch.setattr(deps, "AGENT_API_TOKEN", "")
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {self.AGENT_TOKEN}"},
        )
        assert resp.status_code == 401


class TestTelegramLoginSuccess:
    BOT_TOKEN = "test-bot-token-abc123"

    @pytest.fixture(autouse=True)
    def _set_bot_token(self, monkeypatch):
        import app.auth.routes as auth_routes
        monkeypatch.setattr(auth_routes, "TELEGRAM_BOT_TOKEN", self.BOT_TOKEN)

    @pytest.mark.asyncio
    async def test_valid_login_creates_user_and_returns_token(self, client, db):
        """A genuinely-signed first login creates the user and returns a usable token."""
        payload = sign_telegram_payload(
            self.BOT_TOKEN,
            id=555001,
            first_name="Vera",
            username="vera",
            auth_date=1700000000,
        )

        resp = await client.post("/api/auth/telegram", json=payload)

        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["first_name"] == "Vera"

        created = await User.find_one(User.telegram_id == 555001)
        assert created is not None
        assert created.first_name == "Vera"

    @pytest.mark.asyncio
    async def test_repeat_login_updates_profile_without_duplicating(self, client, db):
        """Logging in again with the same Telegram id refreshes the profile, not a 2nd user."""
        existing = User(telegram_id=555002, first_name="Old", username="old")
        await existing.insert()

        payload = sign_telegram_payload(
            self.BOT_TOKEN,
            id=555002,
            first_name="New",
            username="new",
            auth_date=1700000100,
        )

        resp = await client.post("/api/auth/telegram", json=payload)

        assert resp.status_code == 200
        users = await User.find(User.telegram_id == 555002).to_list()
        assert len(users) == 1
        assert users[0].first_name == "New"
        assert users[0].username == "new"


class TestVerifyTelegramAuth:
    """Unit tests for the HMAC verifier — the auth gate's core contract."""

    BOT_TOKEN = "unit-bot-token-xyz"

    def test_accepts_a_genuinely_signed_payload(self):
        payload = sign_telegram_payload(
            self.BOT_TOKEN, id=42, first_name="Real", auth_date=1700000000
        )
        assert verify_telegram_auth(payload, self.BOT_TOKEN) is True

    def test_rejects_a_payload_tampered_after_signing(self):
        payload = sign_telegram_payload(
            self.BOT_TOKEN, id=42, first_name="Real", auth_date=1700000000
        )
        payload["id"] = 9999  # flip a field, keep the old hash
        assert verify_telegram_auth(payload, self.BOT_TOKEN) is False

    def test_rejects_a_payload_with_no_hash(self):
        assert verify_telegram_auth({"id": 42, "first_name": "Real"}, self.BOT_TOKEN) is False
