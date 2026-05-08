---
id: S02-ASSESSMENT
slice: S02
milestone: M003
assessed_at: 2026-03-14
verdict: roadmap_unchanged
---

# Roadmap Assessment After S02

## Verdict: Roadmap Unchanged

S02 delivered exactly what was planned. S03 remains the correct next slice with no reordering, merging, or scope changes needed.

## Risk Retirement Check

- **vue-i18n reactivity** (medium risk): Retired. Reactive locale switching verified live in browser — heading, nav labels, and feedback text all switch instantly on toggle; backend persistence confirmed via GET /api/settings/language.
- **Settings UI surface** (medium risk): Retired. Settings view ships as 5th gear nav tab; language toggle is discoverable and functional.
- **Seed upsert safety** (high risk): Already retired in S01. Unaffected by S02.

## Success Criterion Coverage

| Criterion | Status |
|-----------|--------|
| User sets language to Russian → exercise names and muscle group labels render in Russian throughout all views | → S03 (names + muscle group filter labels) |
| User refreshes → language preference restored from backend | ✅ Proved in S02 |
| Exercise list shows ~20–30 entries per muscle group | ✅ Proved in S01 |
| Tapping exercise with GIF URL shows GIF inline; no broken image otherwise | → S03 |
| User sets language to English → all labels revert | ✅ Proved in S02 |
| `uv run pytest tests/ -q` passes (≥59 tests) | ✅ Proved in S01 (S03 is frontend-only) |

All criteria have at least one owner. Coverage check passes.

## Boundary Contract Accuracy

S03 consumes from S02:
- `name_ru` and `gif_url` optional fields on Exercise TS type → **present** (added in T02)
- `useSettingsStore().language` reactive ref → **present** (synced to backend)
- `t()` via vue-i18n, `useI18n()` composable → **present** (legacy:false, fully reactive)
- `muscle_groups.*` locale keys in en.ts/ru.ts → **present** (all 6 muscle groups keyed)
- i18n instance at `src/plugins/i18n.ts` → **present** (exported as plain module)

All boundary contracts hold. S03 can consume all listed artifacts without changes.

## One Deviation: Early Type Fix

`Exercise.id` TypeScript type fix (number → string) was listed as S03 scope in the roadmap but was completed in S02 at zero marginal cost (while already touching types/index.ts). S03's scope is reduced by this one item — no remediation needed, just noting it. The Milestone DoD item "Exercise.id TypeScript type fixed from number to string" is already satisfied.

## Requirement Coverage

No Active requirements in REQUIREMENTS.md map to M003 (all are new capabilities). No requirement status changes from S02. Coverage remains sound.

## Conclusion

S03 proceeds as written: wire `name_ru` in ExercisesView, ExerciseCard, ExerciseHistoryView, and WorkoutCard; wire `gif_url` with null handling; wire `t('muscle_groups.' + group)` for filter labels. All infrastructure is in place.
