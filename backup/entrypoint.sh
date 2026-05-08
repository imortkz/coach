#!/usr/bin/env bash
# Backup sidecar entrypoint. Runs backup.sh once per hour in a foreground
# loop so all output lands in `docker compose logs backup`.
#
# Pattern mirrors the certbot service in docker-compose.prod.yml — bash
# loop with sleep is simpler than installing cron, and the consistency
# helps anyone reading the stack.

set -euo pipefail

# Make sure the host bind-mount has the layout we expect. Idempotent.
mkdir -p /backups/hourly /backups/daily

echo "[backup-entrypoint] starting backup loop (hourly cadence, daily promotion at midnight UTC)"

# Trap SIGTERM so `docker compose down` exits cleanly.
trap 'echo "[backup-entrypoint] received TERM, exiting"; exit 0' TERM

# Run an immediate backup on startup so a freshly-deployed stack always
# has at least one archive on disk before the first hour ticks.
/usr/local/bin/backup.sh || echo "[backup-entrypoint] startup backup failed (will retry next cycle)"

while :; do
  # Sleep in the background so the TERM trap fires immediately on shutdown
  # rather than waiting for the full hour.
  sleep 1h &
  wait $!
  /usr/local/bin/backup.sh || echo "[backup-entrypoint] backup cycle failed (will retry next cycle)"
done
