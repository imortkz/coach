# M006: MongoDB Backup & Restore — Context

**Gathered:** 2026-03-14
**Status:** Queued — pending auto-mode execution.

## Project Description

GymCoach runs on a VPS via Docker Compose (nginx + FastAPI + MongoDB). Workout and program data lives in a named Docker volume (`mongodb_data`). Currently the only backup path is a one-liner in DEPLOYMENT.md. There is no scheduled backup, no retention management, and no tested restore procedure.

## Why This Milestone

The app stores irreplaceable personal workout history. A VPS disk failure, accidental collection drop, or botched migration would lose everything. Manual backups are documented but never reliably done. Automated scheduled backups with a defined retention policy close this gap. The user-restore path (replay one user's data from a backup into the live DB) provides a practical recovery tool for the most common failure mode on a multi-user system.

## Recommended Best Practices Captured Here

- **mongodump with --gzip** — produces `.archive.gz` files (~3–10× smaller than raw BSON). A full gymcoach dump will be tiny (single-user personal data), so compression is fast and painless.
- **Separate hourly and daily archive directories** — hourly for recent granularity, daily for long-term. Pruning runs after every backup writes.
- **Sidecar container on the Docker network** — `mongo:8.0` image (same as production, same mongodump version) connects to `mongodb:27017` internally. No host-side `docker exec` needed, no coupling to container naming.
- **Retention enforced by find+delete** — `find /backups/hourly -mmin +$((HOURLY_KEEP * 60)) -delete` and equivalent for daily. Simple, auditable, no extra tooling.
- **Atomic write pattern** — write to `.tmp` first, rename on success. Prevents a partial dump from being picked up as valid if the container crashes mid-write.
- **Daily backup = promoted hourly** — at midnight, the hourly backup already written that hour is hard-linked (or copied) into the daily directory. Avoids running mongodump twice.
- **Restore scripts as checked-in shell scripts** — `restore-full.sh` and `restore-user.sh` live in `backup/` directory in the repo. Restore is not a container — it's a one-shot `docker run` command wrapping mongorestore, invoked by the operator.
- **No remote push in this milestone** — local disk only. DEPLOYMENT.md will document a follow-up pattern: `rclone sync /var/backups/gymcoach remote:bucket` for off-site copy, but the plumbing is deferred to a future milestone.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run `docker compose -f docker-compose.prod.yml up -d` and have a `backup` sidecar container start automatically, backing up hourly and daily on schedule
- Inspect `/var/backups/gymcoach/` on the VPS and find timestamped gzipped archive files
- Run `bash restore-full.sh <archive.gz>` to restore the entire gymcoach database from a backup archive
- Run `bash restore-user.sh <archive.gz> <user_id>` to restore a single user's programs, workouts, and settings from a backup archive into the live DB (upsert — overwrites that user's current data)
- Configure retention via `BACKUP_HOURLY_KEEP` and `BACKUP_DAILY_KEEP` env vars in `.env`

### Entry point / environment

- Entry point: `docker-compose.prod.yml` — backup container starts with the stack
- Environment: production VPS (Docker Compose)
- Live dependencies involved: MongoDB container on the `gymcoach` Docker network

## Completion Class

- Contract complete means: backup container runs `mongodump --gzip --archive` on schedule; archives appear in the host mount; pruning removes files beyond retention limits; restore scripts exit 0 against a test archive
- Integration complete means: `restore-full.sh` against a real archive restores all collections; `restore-user.sh` against a real archive upserts the target user's documents without touching other users
- Operational complete means: backup schedule confirmed running via `docker compose logs backup`; retention enforcement confirmed after simulating age-out (via `touch -t` on test files)

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Stack starts with `docker compose -f docker-compose.prod.yml up -d`; `docker compose ps backup` shows running state
- Wait ≤1 minute; `ls /var/backups/gymcoach/hourly/` shows a `.archive.gz` file with a recent timestamp
- `bash restore-full.sh /var/backups/gymcoach/hourly/<archive.gz>` exits 0; `docker exec gymcoach-mongodb-1 mongosh gymcoach --eval "db.exercises.countDocuments()"` returns expected count
- `bash restore-user.sh /var/backups/gymcoach/hourly/<archive.gz> <user_id>` exits 0; the target user's programs and workouts are present in the live DB
- `docker compose logs backup` shows cron schedule lines and backup completion messages
- Create a dummy old archive file with `touch -d "3 days ago"`, trigger pruning, confirm file is removed (hourly retention = 48h)

## Risks and Unknowns

- **mongodump inside a sidecar — same auth** — MongoDB has no auth enabled (no `--username`/`--password` needed). If auth is added in a future milestone, the backup container will need credentials passed as env vars. The plan should make this explicit so the connection string is env-configurable from day one.
- **crond output visibility** — Alpine's `crond` writes to `/var/log/cron` by default, not stdout. The sidecar entrypoint script must redirect cron output to stdout so `docker compose logs backup` is useful. This is a common oversight.
- **Clock alignment for daily promotion** — "Daily backup at midnight" requires the container's timezone to match the operator's expectations. Alpine defaults to UTC. This is fine and should be documented.
- **Restore user-data upsert semantics** — `mongorestore --nsInclude` on a filtered dump handles full-collection restore. For per-user restore, the dump for a single user cannot be expressed with a simple `--nsInclude` — the restore script must pipe the archive through mongodump's `--query` equivalent at restore time. The correct approach: extract the full archive, then use `mongorestore` with `--drop` only on the specific user's documents (delete-then-insert), or use `mongoimport` on a pre-extracted JSON. This needs a clear implementation choice in planning.
- **Archive size growth** — gymcoach is a personal tool with minimal data. 48 × hourly + 30 × daily archives of a ~1MB dump = ~78MB at most. No size risk.
- **Backup container restart policy** — `restart: unless-stopped` means the backup container restarts if it crashes. Since it runs `crond -f` (foreground), any crash would restart correctly. The cron schedule file must be idempotent on restart.

## Existing Codebase / Prior Art

- `../docker-compose.prod.yml` — stack definition; backup service added here; host volume mount `/var/backups/gymcoach:/backups` added to both backup service and potentially as a reference path
- `../docker-compose.yml` — dev compose; backup service NOT added here — dev doesn't need scheduled backups
- `../DEPLOYMENT.md` — existing manual backup one-liner; this milestone replaces/expands it with the full automated + on-demand restore runbook
- `../.env.example` — needs `BACKUP_HOURLY_KEEP`, `BACKUP_DAILY_KEEP` vars documented

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

No existing requirements map directly — this is new operational scope. New capabilities introduced:

- Automated scheduled MongoDB backups with gzip compression and configurable retention
- Operator restore runbook for full-DB and per-user recovery

## Scope

### In Scope

- `backup/` directory in the repo root containing:
  - `Dockerfile` — `mongo:8.0` base, installs `cronie` (or uses Alpine crond), copies entrypoint and cron script
  - `entrypoint.sh` — sets up cron schedule, redirects cron logs to stdout, execs `crond -f`
  - `backup.sh` — runs `mongodump --gzip --archive=<path>.tmp`, renames to final path on success, promotes to daily if midnight, prunes old files
  - `restore-full.sh` — one-shot `docker run` wrapping `mongorestore --gzip --archive --drop` against the live MongoDB container
  - `restore-user.sh` — one-shot script: extracts user documents from archive and upserts into live DB (implementation detail resolved in planning)
- `docker-compose.prod.yml` update: add `backup` service with host volume mount
- `.env.example` update: add `BACKUP_HOURLY_KEEP` (default 48), `BACKUP_DAILY_KEEP` (default 30), `MONGODB_URL` (already exists but backup container needs it too)
- `DEPLOYMENT.md` update: full backup/restore runbook — verifying backup schedule, running restore scripts, off-site copy suggestion (rclone, manual step)
- Dev compose unchanged

### Out of Scope / Non-Goals

- Remote/off-site backup push (S3, R2, Backblaze) — deferred; DEPLOYMENT.md will document the rclone pattern as a manual follow-up
- Encrypted backup archives — out of scope for v1; disk encryption at the VPS level is the right boundary
- Point-in-time recovery — mongodump is snapshot-based, not oplog-based; PITR requires MongoDB Ops Manager or Atlas, overkill for a personal tool
- Web UI for backup/restore management
- Backup of the Docker volume directly (volume snapshot) — mongodump is safer and more portable than volume-level backup for MongoDB
- MongoDB authentication/authorization setup — no auth currently; backup scripts assume no auth; documented as a future concern

## Technical Constraints

- Sidecar image: `mongo:8.0` (same as production MongoDB) — ensures mongodump/mongorestore version compatibility
- Backup archives: `mongodump --gzip --archive=<file>` — single-file gzip archive, easily verified with `mongorestore --dryRun`
- Host mount path: `/var/backups/gymcoach` on the VPS host → `/backups` inside container
- Container connects to `mongodb:27017` on the `gymcoach` Docker network — no host port exposure needed
- Hourly retention enforced by file age: `find /backups/hourly -name "*.archive.gz" -mmin +$((HOURLY_KEEP * 60)) -delete`
- Daily retention: `find /backups/daily -name "*.archive.gz" -mtime +$DAILY_KEEP -delete`
- Restore scripts are standalone shell scripts — operator runs them from the repo directory on the VPS; they use `docker run --rm` to avoid leaving a restore container running
- `crond` output redirected to stdout in entrypoint so `docker compose logs backup` shows all activity

## Integration Points

- `backup` Docker service → `gymcoach` network → `mongodb:27017` — mongodump connects to MongoDB on the internal network
- Host filesystem `/var/backups/gymcoach` → volume mount → restore scripts read archives from the same host path
- `docker-compose.prod.yml` → `backup` service definition, depends_on mongodb (healthy)
- `DEPLOYMENT.md` → operator runbook for scheduled backup verification, manual restore execution, and rclone off-site suggestion

## Open Questions

- **User-restore implementation detail** — Two options: (a) `mongorestore --nsFrom` with a pre-filtered BSON extracted from the archive using `bsondump + mongoimport`, or (b) restore the full archive to a temp DB, then use `mongosh` to `db.collection.find({user_id}).forEach(insertOrReplace)` into the live DB. Option (b) is simpler to implement and easier to verify. Planning should make the explicit call.
- **Crontab timing** — Hourly: `0 * * * *`. Daily promotion at midnight: `0 0 * * *`. These are UTC. Should be documented in DEPLOYMENT.md so operators in other timezones know what to expect.
