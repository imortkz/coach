# S10: Cleanup — UAT

**Milestone:** M001
**Written:** 2026-03-13

## Smoke Tests

```bash
# 1. passlib gone
grep passlib /path/to/backend/pyproject.toml   # no output

# 2. Tests still pass
cd ../backend && uv run pytest tests/ -q       # 59 passed

# 3. scripts/ deleted
ls ../scripts/                                  # No such file or directory

# 4. Docker builds on Python 3.13
docker build -t test ../backend
docker run --rm test python --version           # Python 3.13.x
docker rmi test
```

All four must pass. No behavioral changes — this slice is purely mechanical cleanup.
