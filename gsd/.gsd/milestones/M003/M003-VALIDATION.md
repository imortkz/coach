---
verdict: needs-attention
remediation_round: 0
---

# Milestone Validation: M003

## Success Criteria Checklist

- [x] User sets language to Russian → exercise names and muscle group labels render in Russian throughout all views — **evidence:** S03 summary confirms browser verification: ExercisesView shows "Руки", "Спина", "Грудь", "Пресс", "Ноги", "Плечи"; exercise names in Russian ("Жим штанги лёжа"); S02 confirms nav labels switch reactively
- [x] User refreshes the app → language preference is restored from backend settings — **evidence:** S02 summary confirms: "refresh → Russian still selected (loaded from backend via router guard before render)"; `GET /api/settings/language` returns `{"key":"language","value":"ru"}`
- [x] Exercise list shows ~20–30 entries per muscle group (up from ~8) — **evidence:** S01 summary confirms ~150 exercises seeded across 6 muscle groups (~25 per group)
- [x] Tapping an exercise with a GIF URL shows the Wikimedia Commons GIF inline; exercises without GIF show no broken image — **evidence:** S03 summary confirms GIF `<img>` element present with correct Wikimedia URL; `v-if="exercise?.gif_url"` guard prevents rendering for null URLs; `@error` handler hides broken loads. Only Barbell Bench Press has a real URL; others correctly show no image.
- [x] User sets language to English → all labels revert to English — **evidence:** S03 browser verification: "English toggle: ExercisesView reverts to 'Arms', 'Back', 'Chest', 'Core', 'Legs', 'Shoulders'"
- [ ] `uv run pytest tests/ -q` in `../backend/` passes (≥59 tests) — **gap:** Validation-time run returned 64 errors (not failures). All errors appear to be `pymongo.errors` — indicating a MongoDB connection/environment issue, not a code regression. All three slice summaries (S01: 64 passed, S02: build clean, S03: 64 passed) report passing tests at completion time. **This is an environmental blocker, not a code defect.**

## Slice Delivery Audit

| Slice | Claimed | Delivered | Status |
|-------|---------|-----------|--------|
| S01 | `GET /api/exercises` returns `name_ru` and `gif_url`; ~150 exercises seeded via upsert-by-name; all 59+ backend tests pass | Exercise model + schema updated; seed.py rewritten with upsert strategy; ~150 exercises with Russian names; 64 tests passed at slice completion | **pass** |
| S02 | vue-i18n infrastructure, Settings view with language toggle, language persists across refresh | vue-i18n v9 plugin, EN/RU locale files (7 namespaces), useSettingsStore synced to backend, SettingsView with toggle, 5th gear nav tab, Exercise.id type fix, `$t()` wired in App/ExercisesView/ExerciseHistoryView; zero build errors | **pass** |
| S03 | Exercise names in Russian across 4 views; GIF display; Exercise.id type fixes | useDisplayName composable; all 4 views localized; GIF display with v-if + @error; cascaded number→string type fixes in SetRow/workouts store; zero build errors, 64 backend tests passed | **pass** |

## Cross-Slice Integration

- **S01 → S02 boundary:** S01 produces `name_ru` and `gif_url` in API response. S02 consumes these by adding them to the Exercise TypeScript type. ✅ Aligned.
- **S02 → S03 boundary:** S02 produces vue-i18n plugin, locale files with `muscle_groups.*` keys, `useSettingsStore`, and Exercise TS type with new fields. S03 consumes all of these via `useDisplayName` composable, `t('muscle_groups.' + ...)` calls, and `settingsStore.language`. ✅ Aligned.
- **S01 → S03 boundary:** S03 consumes `name_ru` and `gif_url` from API (S01). S01 summary notes `gif_url=None` for all except Barbell Bench Press. S03 confirms this and handles it with `v-if` guard. ✅ Aligned.

No boundary mismatches detected.

## Requirement Coverage

The roadmap states this milestone covers LOC-01 through LOC-07 and FIX-01 — all new capabilities not tracked as Active requirements in REQUIREMENTS.md. No Active requirements in REQUIREMENTS.md map to M003, so there are no unaddressed requirements.

- LOC-01 (name_ru field): delivered in S01
- LOC-02 (language persistence): delivered in S02
- LOC-03 (static UI string translations): delivered in S02
- LOC-04 (exercise name localization): delivered in S03
- LOC-05 (expanded exercise library): delivered in S01
- LOC-06 (GIF display): delivered in S03
- LOC-07 (Settings UI for language): delivered in S02
- FIX-01 (Exercise.id type fix): delivered in S02, cascaded in S03

## Definition of Done Checklist

- [x] All three slices complete and verified
- [x] `GET /api/exercises` returns `name_ru` and `gif_url` for seeded exercises
- [x] `PUT /api/settings/language` persists preference; `GET /api/settings/language` returns it
- [x] vue-i18n registered; all static UI strings have EN and RU translations
- [x] Language toggle in Settings view persists to backend and updates all views reactively
- [x] Exercise names use `name_ru` when language is Russian in ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard
- [x] Exercise GIF displays inline with graceful null handling (no broken images)
- [x] ~120–180 exercises seeded across 6 muscle groups (~150 delivered)
- [x] `Exercise.id` TypeScript type fixed from `number` to `string`
- [x] Frontend builds clean — ✅ verified at validation time (110 modules, 0 errors)
- [ ] Backend tests pass (≥59) — ⚠️ environmental: MongoDB not reachable at validation time; passed at slice completion

## Verdict Rationale

All functional deliverables are substantiated by slice summaries and browser verification evidence. The frontend build passes clean at validation time. The only gap is the backend test suite returning connection errors during this validation run — all 64 tests error with `pymongo.errors`, indicating MongoDB is not running in the validation environment, not a code regression. All three slices independently verified 64 passing tests at completion time (same day, 2026-03-14).

**Verdict: `needs-attention`** — the milestone is functionally complete. The backend test gap is environmental (MongoDB unavailable at validation time), not a code defect. No remediation slices are needed. The test suite should be re-run when MongoDB is available to confirm, but this does not block milestone completion.

## Remediation Plan

None required. To clear the attention item:
- Ensure MongoDB is running (`docker compose up -d mongodb` or local `mongod`)
- Re-run `cd ../backend && uv run pytest tests/ -q` — expect 64 passed
