/// <reference types="node" />
import { describe, expect, it } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, relative, resolve } from 'node:path'

// Static source guard for the issue #20 bug class: ids in this codebase are
// UUID strings. Coercing an id to a number (Number(...id), parseInt(...id),
// +id) turns the UUID into NaN and produces requests like /api/programs/NaN,
// a silent prod 404. This test scans the frontend source and fails if any id
// field — or route.params.id — is run through numeric coercion.
//
// Scoped narrowly so it does NOT flag legitimate numeric coercion of non-id
// values, e.g. ProgramEditView.vue's `Number(...target_weight_kg)` (a weight).

const srcDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const root = resolve(srcDir, '..')

// Match numeric coercion applied to an id-ish expression:
//   Number(route.params.id)         -> route.params.id
//   parseInt(program.id)            -> *.id
//   Number(exercise_id)             -> *_id  / bare _id
//   parseInt(programId)             -> *Id identifier
// We deliberately require the coerced argument to END in an id token so a
// weight/reps argument never matches.
// Note we intentionally do NOT match unary `+id`: in this codebase ids are
// only ever concatenated into URL strings ('/x/' + id), and a `+ id` arm
// false-positives on that legitimate concatenation. Number()/parseInt() are
// the real, idiomatic coercion calls and the actual #20 failure mode.
const PATTERNS = [
  // Number(...) / parseInt(...) wrapping an id field or route.params.id
  /\b(?:Number|parseInt)\s*\(\s*[\w.[\]'"]*?(?:route\.params\.id|\bparams\.id|\w*_id|\.id|\bid|\w*Id)\b/,
]

function* walk(dir: string): Generator<string> {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'test') continue // don't scan the tests themselves
      yield* walk(p)
    } else if (entry.isFile() && /\.(ts|vue)$/.test(entry.name)) {
      yield p
    }
  }
}

describe('no numeric coercion of UUID ids (issue #20 guard)', () => {
  it('does not coerce any id field or route.params.id to a number anywhere in src/', () => {
    const violations: string[] = []
    for (const abs of walk(srcDir)) {
      const rel = relative(root, abs).replaceAll('\\', '/')
      const text = readFileSync(abs, 'utf8')
      text.split('\n').forEach((line, i) => {
        if (PATTERNS.some((re) => re.test(line))) {
          violations.push(`${rel}:${i + 1}: ${line.trim()}`)
        }
      })
    }

    expect(violations, `Numeric coercion of id fields found:\n${violations.join('\n')}`).toEqual([])
  })

  it('the guard regex does flag a known-bad pattern (self-check) and spares weights', () => {
    const bad = [
      'const programId = Number(route.params.id)',
      'const x = parseInt(program.id)',
      'fetchProgram(Number(exercise_id))',
    ]
    const good = [
      'set.target_weight_kg = Number(value)',
      'const programId = String(route.params.id)',
      'const reps = Number(input.value)',
      ":to=\"'/exercises/' + exercise.id + '/history'\"", // string concat, not coercion
    ]
    for (const line of bad) {
      expect(PATTERNS.some((re) => re.test(line)), `should flag: ${line}`).toBe(true)
    }
    for (const line of good) {
      expect(PATTERNS.some((re) => re.test(line)), `should NOT flag: ${line}`).toBe(false)
    }
  })
})
