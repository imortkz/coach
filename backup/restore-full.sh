#!/usr/bin/env bash
# Full-DB restore from a backup archive.
#
# Usage:
#   bash backup/restore-full.sh /var/backups/gymcoach/hourly/<archive>.archive.gz
#
# Reverts the live `gymcoach` database to the state captured in the
# archive. `--drop` per-collection is applied so any documents added
# after the archive was taken are removed.
#
# This is intentionally a one-shot `docker run --rm` against a fresh
# `mongo:8.0` container that joins the `gymcoach` Docker network and
# talks to the live `mongodb` service. No persistent state, no leftover
# container after the script exits.
#
# Run from the repo root on the VPS so the relative paths resolve.

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <archive-path>"
  exit 1
fi

archive="$1"

if [ ! -f "${archive}" ]; then
  echo "ERROR: archive not found: ${archive}" >&2
  exit 1
fi

archive_abs="$(readlink -f "${archive}")"
archive_dir="$(dirname "${archive_abs}")"
archive_name="$(basename "${archive_abs}")"

MONGODB_URL="${MONGODB_URL:-mongodb://mongodb:27017}"
MONGODB_DB_NAME="${MONGODB_DB_NAME:-gymcoach}"
NETWORK="${BACKUP_DOCKER_NETWORK:-gymcoach_gymcoach}"

echo "[restore-full] archive: ${archive_abs}"
echo "[restore-full] target:  ${MONGODB_URL} db=${MONGODB_DB_NAME}"
echo "[restore-full] network: ${NETWORK}"
echo "[restore-full] WARNING: --drop is enabled. The live ${MONGODB_DB_NAME} database will be reverted to the archive snapshot."

read -r -p "Continue? [y/N] " confirm
if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ]; then
  echo "[restore-full] aborted"
  exit 1
fi

docker run --rm \
  --network "${NETWORK}" \
  -v "${archive_dir}:/restore:ro" \
  mongo:8.0 \
  mongorestore \
    --uri "${MONGODB_URL}" \
    --db "${MONGODB_DB_NAME}" \
    --gzip \
    --archive="/restore/${archive_name}" \
    --drop

echo "[restore-full] done. Verify with:"
echo "  docker compose -f docker-compose.prod.yml exec mongodb mongosh ${MONGODB_DB_NAME} --eval 'db.exercises.countDocuments()'"
