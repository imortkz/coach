# Queue

<!-- Append-only log of queued milestones -->

| Date | ID | Title | Notes |
|------|----|-------|-------|
| 2026-03-14 | M002 | Workout Set UX Fixes | Frontend-only. Fix Edit button no-op on unlogged extra sets; add swipe-to-skip on template sets (session only, undo toast); no backend changes. |
| 2026-03-14 | M003 | Localization, Expanded Exercise Library & Exercise GIFs | EN/RU language toggle persisted via existing settings API. Add name_ru + gif_url to Exercise model + seed. Expand seed to ~20-30 exercises per group. vue-i18n for static UI strings. Wikimedia Commons GIF URLs (no self-hosting). |
| 2026-03-14 | M004 | SSL/HTTPS with Let's Encrypt | Certbot sidecar container in docker-compose.prod.yml. HTTP-01 ACME challenge via nginx webroot. nginx gains 443 block + HTTP→HTTPS redirect. Autorenew via crond. Dev compose unchanged. |
| 2026-03-14 | M005 | Progress Report | New GET /api/workouts/report?weeks=N endpoint (Python aggregation). Volume by muscle group per week (stacked bar), workout frequency per week (bar), PR table. /report frontend route. 4-week default, configurable. Chart.js/vue-chartjs already installed. |
| 2026-03-14 | M006 | MongoDB Backup & Restore | Docker sidecar (mongo:8.0) with crond. Hourly + daily mongodump --gzip --archive. Retention: 48 hourly, 30 daily (configurable via env). restore-full.sh and restore-user.sh scripts. Host mount /var/backups/gymcoach. Dev compose unchanged. |
| 2026-03-14 | M007 | Localization Coverage Completion | M003 gap fix. useDisplayName not wired in ProgramEditView; hardcoded English in ProgramsView, ProgramPicker, WorkoutSummary, ActiveWorkout. ~30 new locale keys. Russian pluralization for exercise count. Frontend-only. |
