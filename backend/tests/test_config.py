"""Tests for config.py security contracts.

Verifies fail-fast boot behaviour and safe defaults — these tests exercise
observable contracts, not internal implementation details.
"""

import os
import subprocess
import sys


class TestDevModeDefault:
    def test_dev_mode_defaults_to_false_without_env(self):
        """DEV_MODE is false when the env var is absent — must opt in, not opt out."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import os; os.environ.pop('DEV_MODE', None); os.environ.pop('JWT_SECRET', None); "
                "os.environ['JWT_SECRET'] = 'some-secret'; "
                "import importlib, app.config as m; importlib.reload(m); "
                "print(m.DEV_MODE)",
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__) + "/..",
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "False"


class TestJwtSecretFailFast:
    def test_no_jwt_secret_no_dev_mode_raises_at_import(self):
        """When DEV_MODE is off and JWT_SECRET is unset the app refuses to boot."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import os; os.environ['DEV_MODE'] = 'false'; "
                "os.environ.pop('JWT_SECRET', None); "
                "import app.config",
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__) + "/..",
        )
        assert result.returncode != 0, "Expected import to raise but it succeeded"
        assert "RuntimeError" in result.stderr
        assert "JWT_SECRET" in result.stderr

    def test_jwt_secret_set_and_dev_mode_off_imports_fine(self):
        """When JWT_SECRET is provided and DEV_MODE is off the app boots and uses the env value."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import os; os.environ['DEV_MODE'] = 'false'; "
                "os.environ['JWT_SECRET'] = 'my-prod-secret'; "
                "import app.config as m; "
                "print(m.JWT_SECRET)",
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__) + "/..",
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "my-prod-secret"
