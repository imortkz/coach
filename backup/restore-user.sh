#!/usr/bin/env bash
# Restore a single user's documents from a backup archive into the live
# database without touching other users.
#
# Usage:
#   bash backup/restore-user.sh /var/backups/gymcoach/hourly/<archive>.archive.gz <user_id>
#
# Two-phase restore:
#   1. mongorestore the entire archive into a sandbox database
#      `gymcoach_restore_<ts>` on the live mongo. The sandbox is
#      side-by-side with the production database; nothing in production
#      changes during this phase.
#   2. mongosh script: for each user-scoped collection, find the target
#      user's documents in the sandbox and upsert them by _id into the
#      live `gymcoach` database. Documents owned by other users are
#      ignored. Documents that exist in the live DB but not in the
#      archive (i.e. were created after the snapshot) are NOT removed
#      — this preserves any post-snapshot data the user has accumulated.
#      If you want strict snapshot semantics, do a delete-then-upsert
#      manually.
#   3. Drop the sandbox database.
#
# Collections targeted: programs, workouts, settings (user_id field),
# users (id == user_id). Exercises are intentionally excluded — shared
# seeds (user_id=None) and other users' custom exercises must not be
# touched.
#
# Run from the repo root on the VPS.

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <archive-path> <user_id>"
  exit 1
fi

archive="$1"
user_id="$2"

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

ts="$(date -u +%Y%m%d%H%M%S)"
sandbox_db="${MONGODB_DB_NAME}_restore_${ts}"

echo "[restore-user] archive:  ${archive_abs}"
echo "[restore-user] user_id:  ${user_id}"
echo "[restore-user] target:   ${MONGODB_URL} db=${MONGODB_DB_NAME}"
echo "[restore-user] sandbox:  ${sandbox_db}"
echo "[restore-user] network:  ${NETWORK}"
echo "[restore-user] live ${MONGODB_DB_NAME} will receive an UPSERT of this user's documents (other users untouched)."

read -r -p "Continue? [y/N] " confirm
if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ]; then
  echo "[restore-user] aborted"
  exit 1
fi

# Phase 1 — restore the full archive into the sandbox DB. mongorestore's
# --nsFrom/--nsTo rewrites the namespace prefix during restore so the
# archive's `gymcoach.*` collections land as `<sandbox>.*` instead.
echo "[restore-user] phase 1: restoring archive into sandbox ${sandbox_db}"
docker run --rm \
  --network "${NETWORK}" \
  -v "${archive_dir}:/restore:ro" \
  mongo:8.0 \
  mongorestore \
    --uri "${MONGODB_URL}" \
    --gzip \
    --archive="/restore/${archive_name}" \
    --nsFrom "${MONGODB_DB_NAME}.*" \
    --nsTo "${sandbox_db}.*"

# Phase 2 — upsert this user's documents from the sandbox into live.
# We run a mongosh script in a one-shot container. The script iterates
# over the four user-scoped collections, finds documents belonging to
# the target user_id, and replaces-by-_id in the live DB.
echo "[restore-user] phase 2: upserting user ${user_id} documents into live DB"
docker run --rm \
  --network "${NETWORK}" \
  mongo:8.0 \
  mongosh "${MONGODB_URL}" --quiet --eval "
    const sandbox = db.getSiblingDB('${sandbox_db}');
    const live    = db.getSiblingDB('${MONGODB_DB_NAME}');
    const userId  = '${user_id}';

    // Each entry: collection name + filter to find this user's documents
    // in the sandbox copy. 'users' uses _id == userId because the user
    // document is itself keyed on the user id; the others use user_id
    // as a normal field.
    const targets = [
      { name: 'users',    filter: { _id: userId } },
      { name: 'programs', filter: { user_id: userId } },
      { name: 'workouts', filter: { user_id: userId } },
      { name: 'settings', filter: { user_id: userId } },
    ];

    for (const t of targets) {
      const docs = sandbox.getCollection(t.name).find(t.filter).toArray();
      if (docs.length === 0) {
        print('  ' + t.name + ': no documents in archive for user ' + userId);
        continue;
      }
      const ops = docs.map((doc) => ({
        replaceOne: {
          filter: { _id: doc._id },
          replacement: doc,
          upsert: true,
        },
      }));
      const res = live.getCollection(t.name).bulkWrite(ops);
      print('  ' + t.name + ': matched=' + res.matchedCount + ' modified=' + res.modifiedCount + ' upserted=' + res.upsertedCount);
    }

    // Phase 3 — drop the sandbox to free disk.
    print('[restore-user] dropping sandbox ${sandbox_db}');
    sandbox.dropDatabase();
  "

echo "[restore-user] done. Verify with:"
echo "  docker compose -f docker-compose.prod.yml exec mongodb mongosh ${MONGODB_DB_NAME} --eval 'db.workouts.countDocuments({ user_id: \"${user_id}\" })'"
echo
echo "If the script aborted between phase 1 and phase 3, the sandbox DB ${sandbox_db} may be left behind. Drop manually with:"
echo "  docker compose -f docker-compose.prod.yml exec mongodb mongosh --eval 'db.getSiblingDB(\"${sandbox_db}\").dropDatabase()'"
