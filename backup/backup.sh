#!/usr/bin/env bash
# Run a single backup cycle:
#  1. mongodump --gzip --archive into /backups/hourly/.tmp.archive.gz
#  2. atomically rename to /backups/hourly/<ts>.archive.gz
#  3. if the current hour is 00 UTC, copy that file into /backups/daily/
#  4. prune /backups/hourly older than $BACKUP_HOURLY_KEEP hours
#  5. prune /backups/daily older than $BACKUP_DAILY_KEEP days
#
# Atomic rename (step 2) means a partial dump from a crashed run never
# appears as a valid archive; the .tmp file just sits around until the
# next successful run cleans it up (the `find -delete` for hourly will
# eventually catch it via age).

set -euo pipefail

MONGODB_URL="${MONGODB_URL:-mongodb://mongodb:27017}"
MONGODB_DB_NAME="${MONGODB_DB_NAME:-gymcoach}"
BACKUP_HOURLY_KEEP="${BACKUP_HOURLY_KEEP:-48}"
BACKUP_DAILY_KEEP="${BACKUP_DAILY_KEEP:-30}"

ts="$(date -u +%Y%m%dT%H%M%SZ)"
hour_utc="$(date -u +%H)"

archive_name="${MONGODB_DB_NAME}-${ts}.archive.gz"
hourly_path="/backups/hourly/${archive_name}"
tmp_path="/backups/hourly/.tmp.${archive_name}"
daily_path="/backups/daily/${archive_name}"

echo "[backup ${ts}] dumping ${MONGODB_DB_NAME} from ${MONGODB_URL} → ${hourly_path}"

# mongodump writes archive bytes to the file given by --archive=<path>.
# --gzip applies on-the-fly compression. --quiet keeps non-error output
# off stdout so our own log lines aren't drowned.
mongodump \
  --uri "${MONGODB_URL}" \
  --db "${MONGODB_DB_NAME}" \
  --gzip \
  --archive="${tmp_path}" \
  --quiet

mv "${tmp_path}" "${hourly_path}"

archive_size="$(du -h "${hourly_path}" | cut -f1)"
echo "[backup ${ts}] hourly archive written (${archive_size})"

# Daily promotion: at the top of midnight UTC, copy the archive we just
# wrote into the daily/ directory. Copy rather than hard-link to avoid
# any concern about cross-filesystem semantics on the bind-mount.
if [ "${hour_utc}" = "00" ]; then
  cp "${hourly_path}" "${daily_path}"
  echo "[backup ${ts}] promoted to daily archive"
fi

# Retention pruning. Use -mmin (minutes) for hourly precision and
# -mtime (days) for daily. -delete is racy in pathological setups but
# fine here — only one backup container writes this directory.
pruned_hourly="$(find /backups/hourly -maxdepth 1 -name '*.archive.gz' -type f -mmin "+$((BACKUP_HOURLY_KEEP * 60))" -delete -print | wc -l)"
pruned_daily="$(find /backups/daily -maxdepth 1 -name '*.archive.gz' -type f -mtime "+${BACKUP_DAILY_KEEP}" -delete -print | wc -l)"

if [ "${pruned_hourly}" != "0" ] || [ "${pruned_daily}" != "0" ]; then
  echo "[backup ${ts}] pruned: hourly=${pruned_hourly}, daily=${pruned_daily}"
fi

# Also sweep any stale .tmp files left over from a previously crashed run.
find /backups/hourly -maxdepth 1 -name '.tmp.*' -type f -mmin +60 -delete 2>/dev/null || true

echo "[backup ${ts}] done"
