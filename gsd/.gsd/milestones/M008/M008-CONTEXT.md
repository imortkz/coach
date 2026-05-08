# M008: CI/CD — Context

**Gathered:** 2026-05-08
**Status:** Queued — scope agreed in chat 2026-05-08, awaiting implementation.

## Project Description

GymCoach is a personal gym training companion (FastAPI/Beanie/MongoDB backend + Vue 3/Vite/Tailwind frontend, served via nginx multi-stage in front of `/api/*` proxy). Through M001–M007 the project has accumulated a working test suite (~67 backend tests, 3 of them new in M005), a Vue type-checked codebase, and an HTTPS production deployment on `coach.imort.kz`. So far, all deploys have been manual — `rsync` to VPS + `docker compose up --build -d` over ssh. There is no automated test gate on PRs; merging to `master` does not trigger anything.

## Why This Milestone

Two pains that compound on each other:

1. **No PR gate.** Every PR has been manually verified — backend tests run on the dev's machine (or via the makeshift `docker run` against an ephemeral mongo), and frontend changes are eyeballed in the browser. As the project grows this becomes the limiting factor on review confidence.
2. **Manual deploy.** Every merge requires the dev to ssh in and `docker compose up --build -d`. This bottlenecks the merge-to-prod feedback loop, and makes "I'll fix it after lunch" a much heavier sentence than it should be for a pet project.

This milestone closes both gaps with a baseline GitHub Actions setup and a one-shot ssh-based auto-deploy. Per the dev's preference (2026-05-08 chat), staging environments and image registries are explicitly out of scope — they're the right answer eventually, but premature for this codebase's scale.

## User-Visible Outcome

### When this milestone is complete:

- Every PR opened against `master` automatically runs the backend test suite (with MongoDB in an Actions service container) and the frontend type-check + build. The PR shows pass/fail status checks, blocking merge if either fails.
- Every push to `master` (after CI passes) automatically ssh'es to the VPS and reloads the `docker compose -f docker-compose.prod.yml` stack with the new code. Within ~2–3 minutes of merge, prod reflects the change.
- Dependabot opens PRs on a regular cadence to bump npm, uv/pip, docker, and `actions/*` versions. The dev decides which to merge.
- README displays badges showing the live status of CI and deploy workflows.
- After the first deploy workflow has merged successfully, the dev enables branch protection on `master` (PR-only, required status checks). All future changes go through PRs.

### Entry points / environment

- GitHub Actions runners (ubuntu-latest)
- VPS `coach@46.225.110.147`, hostname `coach.imort.kz`
- Existing prod stack: `docker-compose.prod.yml` with mongodb / backend / nginx / certbot services

## Completion Class

- **Contract complete** means: `.github/dependabot.yml`, `.github/workflows/ci.yml`, and `.github/workflows/deploy.yml` exist; `ci.yml` runs on `pull_request` and `push: master`, `deploy.yml` runs on `workflow_run: ci.yml completed && conclusion == success && head_branch == master`.
- **Integration complete** means: a deliberate test PR opened against `master` triggers `ci.yml` and produces visible status checks; on merge, `deploy.yml` runs and the VPS stack is rebuilt; README badges update to reflect those runs.
- **Operational complete** means: branch protection on `master` is enabled with `ci.yml` as a required status check; dependabot has opened at least one PR (proves config is valid).

## Final Integrated Acceptance

To call this milestone complete, the following must be demonstrably true:

- `ci.yml` backend job runs `pytest` against the existing 67 tests (MongoDB service container on port 27017) and reports green.
- `ci.yml` frontend job runs `npm ci` + `vue-tsc --noEmit` + `npm run build` and produces no type errors.
- A PR with a deliberately-broken test fails `ci.yml` and blocks merge (proves the gate works).
- After merging a no-op PR to `master`, `deploy.yml` ssh's into the VPS, runs `git fetch && git reset --hard origin/master && docker compose -f docker-compose.prod.yml up --build -d`, and `https://coach.imort.kz/api/health` returns 200 within 5 minutes.
- README contains two badges (`ci.yml`, `deploy.yml`) and they reflect the current status.
- Branch protection is configured on `master` (visible in repo settings).
- Dependabot has opened at least one update PR.

## Risks and Unknowns

- **The bootstrap chicken-and-egg.** Branch protection cannot be enabled until *after* the first `deploy.yml` PR is merged, because turning on PR-only first would mean we can't merge the very PR that introduces the deploy workflow without it failing the not-yet-existing required check. Sequence is: PR with CI + deploy → manually merged → confirm prod updates → THEN dev enables branch protection. Documented here so we don't accidentally invert it.
- **The first deploy will rebuild over the existing manually-deployed stack** without coordination. Since the VPS `git reset --hard origin/master` matches what we've been doing manually, this should be a no-op. Risk is low but non-zero — verify after first run.
- **MongoDB version drift between CI service container and prod.** Prod is `mongo:8.0`; CI service container should pin the same. If we let CI use `mongo:latest` we set up a flake source for later.
- **uv/pip cache invalidation.** Caching `~/.cache/uv` keyed on `uv.lock` hash is correct, but uv has been changing its cache layout; a non-cached run takes ~15 seconds on this dep set, so caching is a nice-to-have, not load-bearing.
- **Frontend build matrix.** Currently only `npm run build` is gated. We don't have unit/component tests on the frontend yet — `vue-tsc --noEmit` catches type regressions but not behavioral. Acceptable for M008 baseline; expanding test coverage is its own future milestone.
- **SSH key handling.** The deploy workflow uses an SSH key stored in repo Secrets (`VPS_SSH_KEY`). Operational risk: if the key is leaked, anyone with read access to the secret can deploy arbitrary code. Mitigation in scope: separate dedicated keypair (not the dev's personal key), pubkey-only on VPS, no shell access beyond what `coach@` user already has. Mitigation NOT in scope: command restrictions in `authorized_keys`, hardware tokens, OIDC-to-cloud — overkill for a pet.
- **Race between CI and deploy.** `deploy.yml` triggered via `workflow_run` after `ci.yml` completes successfully is the correct primitive — the alternative (single workflow with deploy as a job) couples test+deploy timing tighter than necessary. Documented choice.

## Existing Codebase / Prior Art

- `../backend/pyproject.toml` — already declares dev deps (pytest, pytest-asyncio, httpx, ruff) under `[dependency-groups]`. CI's `uv sync` will pull these by default.
- `../backend/tests/conftest.py` — fixtures already point at `mongodb://localhost:27017`, which is what the GitHub Actions service container will expose.
- `../frontend/package.json` — has `vue-tsc` and a `build` script in place; no extra config needed.
- `../docker-compose.prod.yml` — the deploy target. CI does NOT need to use this; it only needs to test the code. The deploy step is a thin ssh wrapper around it.
- `../DEPLOYMENT.md` — current manual deploy doc; will be amended in M008 with a one-line note that production deploys are now automated and the manual flow is the fallback for first-bootstrap or recovery.
- The existing `~/.ssh/coach_actions_deploy` key (generated by Val 2026-05-08, after the chat that produced this CONTEXT) — pubkey already in `~coach/.ssh/authorized_keys` on VPS, privkey in GitHub Secret `VPS_SSH_KEY`.

## Relevant Requirements

No explicit numbered requirements predate this milestone; M008 introduces the operational baseline:

- **R-CI-01**: Backend tests must run automatically on every PR and push to `master`.
- **R-CI-02**: Frontend type-check and build must run automatically on every PR and push to `master`.
- **R-CD-01**: Successful CI on `master` triggers automatic deployment to production.
- **R-OPS-01**: Dependabot opens update PRs on a defined cadence for npm, uv/pip, docker, and github-actions ecosystems.
- **R-OPS-02**: README displays badges for CI and deploy workflow status.

## Scope

### In Scope

- `.github/dependabot.yml` configured for four ecosystems:
  - `npm` in `frontend/`
  - `pip` (or `uv` once dependabot supports it natively) in `backend/`
  - `docker` for both `backend/Dockerfile` and `nginx/Dockerfile`
  - `github-actions` for the workflow files themselves
  - Cadence: weekly (Monday morning), grouped sensibly to avoid PR floods.
- `.github/workflows/ci.yml` with two parallel jobs:
  - **backend**: ubuntu-latest, mongo:8.0 service container on port 27017, python 3.13, install uv, `uv sync --frozen`, `uv run pytest`. uv cache keyed on `uv.lock` hash.
  - **frontend**: ubuntu-latest, node 20, `npm ci`, `vue-tsc --noEmit`, `npm run build`. npm cache keyed on `package-lock.json` hash.
- `.github/workflows/deploy.yml`:
  - Triggered by `workflow_run` of `ci.yml` with `conclusion == success && head_branch == master`.
  - Loads `${{ secrets.VPS_SSH_KEY }}` into ssh-agent.
  - `ssh-keyscan` the VPS host into `known_hosts` (or fail-closed if mismatched).
  - SSHes to `coach@46.225.110.147`, runs `cd /home/coach/coach && git fetch origin && git reset --hard origin/master && docker compose -f docker-compose.prod.yml up --build -d`.
  - Posts a final `curl -fsS https://coach.imort.kz/api/health` health check; if it fails, the workflow fails (loud failure, since broken prod deserves immediate attention).
- README badges section (top of file) showing live status for `ci.yml` and `deploy.yml`.
- Brief amendment to `DEPLOYMENT.md` referencing the automated flow as primary and the manual flow as fallback.
- Commit history of the milestone tagged `[M008]` per repo convention.

### Out of Scope / Non-Goals

- Staging environment or any pre-production deploy stage. Single-track `master → prod` only.
- Image registry (ghcr.io / Docker Hub) — VPS rebuilds locally on each deploy.
- Code coverage reports, coverage upload, coverage badges.
- E2E / Playwright / browser-based tests in CI.
- Frontend unit or component tests (we don't have a Vitest/Jest setup; introducing one is its own milestone).
- Slack/Telegram notification on deploy success or failure.
- OIDC-based deploy (hardware-token or cloud-IAM identity for runners).
- Rollback automation. If a deploy goes bad, manual ssh + `git reset --hard <prev>` is the recovery path.
- Branch protection rules themselves are configured by the dev via GitHub UI as the LAST step of M008 (after first successful auto-deploy). The setting is not authored in code; only documented.

## Technical Constraints

- All workflows must run on `ubuntu-latest` runners. No self-hosted runners; no matrix builds across OS.
- `mongo:8.0` exact tag in CI (matches prod). `python:3.13` for backend, `node:20` for frontend.
- Deploy workflow uses `webfactory/ssh-agent` (or equivalent) for ssh-agent loading — no writing the privkey to disk.
- All secrets referenced as `${{ secrets.X }}` — never echoed, never logged.
- `set -e` (or equivalent strict mode) in all multi-command shell steps.
- Concurrency control on `deploy.yml`: at most one deploy at a time; later runs cancel earlier ones queued for the same branch.

## Integration Points

- GitHub Secrets: `VPS_SSH_KEY` (privkey) — already populated by the dev before M008 implementation begins.
- VPS `~coach/.ssh/authorized_keys` — already has the corresponding pubkey appended.
- VPS `/home/coach/coach/` — git working tree, gets `git reset --hard` and `docker compose up --build -d` from the deploy job.
- `docker-compose.prod.yml` — referenced by deploy job; no changes required for M008.
- `README.md` — badges section added at top.
- `DEPLOYMENT.md` — short note pointing to the automated flow.

## Open Questions

- **Frontend lint in CI?** `ruff` is set up for backend in dev deps. Frontend has no eslint config currently. Agreed: skip lint in M008, defer to a future "code quality" milestone.
- **Concurrency cancel-old vs queue?** Defaulting to cancel-old (`cancel-in-progress: true`) on deploy — rapid back-to-back merges to master should converge on the latest. If this proves wrong (e.g. someone counts on each deploy completing for audit), revisit.
- **Health-check timeout in deploy?** First version uses a single `curl -fsS` with default timeouts. If we see flakes from cold-start delay on the rebuilt nginx, add a retry loop (5 × 10s).
