# M006: MongoDB Backup & Restore — Roadmap

**Status:** Active — implementation in progress (2026-05-08).

Implementation plan for [`M006-CONTEXT.md`](./M006-CONTEXT.md). Three
slices, ops/backend-only, no frontend changes.

## Open questions resolved here

**User-restore mechanism (CONTEXT open question).** Going with option
(b): `restore-user.sh` restores the full archive into a sandbox database
(`gymcoach_restore_<timestamp>`) on the live MongoDB instance, then uses
`mongosh` to find the requested user's documents in each collection and
upsert them into the live `gymcoach` DB by `_id`. After restore, the
sandbox DB is dropped. This is simpler to implement than `bsondump +
mongoimport` filtering and easier to verify (operator can inspect the
sandbox DB before deciding). Trade-off: doubles disk use during the
restore window for ~one archive's worth of data; acceptable given a
gymcoach dump is small.

**Loop mechanism.** Going with the bash-loop pattern already used by the
`certbot` service in `docker-compose.prod.yml` (`while :; do ...; sleep
1h & wait; done`) instead of installing `cron` inside the sidecar.
Simpler, consistent with the codebase, no extra apt install, output
naturally goes to stdout. Drift across the hour is acceptable for backup
cadence; daily promotion happens inside `backup.sh` rather than as a
second cron entry.

**Daily promotion.** `cp` rather than `ln` (hardlink). Files are
~1-3MB each so disk cost is negligible (~48 hourly × 1MB + 30 daily ×
1MB ≈ 78MB peak per CONTEXT estimate); copy avoids any concern about
host filesystem hardlink semantics on the bind-mount path.

## S01 — Backup sidecar + compose integration

- New `backup/` directory at repo root with:
  - `Dockerfile` — `FROM mongo:8.0`, `COPY entrypoint.sh backup.sh /usr/local/bin/`, no extra packages.
  - `entrypoint.sh` — `set -e`, ensure `/backups/hourly` and `/backups/daily` exist, then `exec` the bash loop that runs `backup.sh` once per hour.
  - `backup.sh` — does the actual work: `mongodump --gzip --archive` to a `.tmp` path under `hourly/`, atomic rename, midnight-UTC promotion via `cp`, two `find -delete` retention sweeps. Echoes timestamps to stdout for log visibility.
- `docker-compose.prod.yml` — add `backup` service: builds `./backup`, joins `gymcoach` network, depends on `mongodb` (`condition: service_healthy`), bind-mounts `/var/backups/gymcoach` host path → `/backups` in container, env vars `MONGODB_URL`, `MONGODB_DB_NAME`, `BACKUP_HOURLY_KEEP`, `BACKUP_DAILY_KEEP`. `restart: unless-stopped` (matches sibling services).
- Dev compose untouched per CONTEXT.

## S02 — Restore scripts

- `backup/restore-full.sh` — `docker run --rm` against `mongo:8.0`, joins `gymcoach` network, mounts the archive directory read-only, runs `mongorestore --gzip --archive=<file> --drop`. `--drop` is the right semantic here: a full restore reverts the live DB to the archive's state.
- `backup/restore-user.sh` — same `docker run --rm` pattern, two phases:
  1. `mongorestore` the archive into a sandbox DB (`gymcoach_restore_<ts>`) on the live mongo.
  2. `mongosh --eval` script: for each collection in `gymcoach` (programs, workouts, settings, users), find documents matching `user_id == <target>` in the sandbox DB and upsert them by `_id` into the live `gymcoach` DB.
  3. Drop the sandbox DB.
- Both scripts print clear progress + final success/failure lines so the operator can copy-paste output into a runbook entry.

## S03 — Docs + .env.example + verification

- `.env.example` — append `BACKUP_HOURLY_KEEP` (default `48`), `BACKUP_DAILY_KEEP` (default `30`) with comments. `MONGODB_URL` and `MONGODB_DB_NAME` defaults already implicit elsewhere — kept implicit unless the backup service really needs explicit env (which it does, so add `MONGODB_URL=mongodb://mongodb:27017`).
- `DEPLOYMENT.md` — new "Backup & Restore" section documenting:
  - First-time host directory creation (`mkdir -p /var/backups/gymcoach`).
  - How to verify the backup loop (`docker compose logs backup`, `ls /var/backups/gymcoach/hourly/`).
  - How to run `restore-full.sh` and `restore-user.sh` (one-line invocations + what each does).
  - Off-site copy as a manual follow-up (`rclone sync /var/backups/gymcoach remote:bucket`) — pattern only, plumbing intentionally deferred.
  - Existing manual `mongodump` one-liner is removed (superseded).
- Sanity validation: every shell script passes `bash -n`; YAML files round-trip through `yaml.safe_load`; the backup loop logic is verified by reading the script line-by-line against the acceptance list in CONTEXT.

## Out of scope (per M006-CONTEXT)

Remote/off-site push, encrypted archives, point-in-time recovery, web
UI, volume-level backup, MongoDB auth setup. The DEPLOYMENT.md note for
`rclone sync` is the only nod toward off-site, and it's text-only.

## Risks (notes for myself during implementation)

- **TZ for daily promotion.** Container TZ defaults to UTC. Midnight
  UTC ≠ midnight YEKT. Documented in DEPLOYMENT.md so the operator
  isn't surprised when daily archives appear at 05:00 local.
- **mongorestore --drop semantics.** `--drop` per collection drops only
  collections that exist in the archive, not arbitrary unrelated
  collections in the live DB. For our schema (programs, workouts,
  settings, users, exercises), this is exactly the desired behaviour.
- **Sandbox DB cleanup on restore-user failure.** If `mongorestore` to
  the sandbox succeeds but the upsert step fails, the sandbox DB is
  left behind. Script prints a clear hint at the end:
  `db.gymcoach_restore_<ts>.dropDatabase()` to clean up manually.
