#!/usr/bin/env node
// Static guard: no raw `fetch('/api/...')` calls outside the allowlist.
//
// A raw fetch() to a backend endpoint bypasses src/lib/apiFetch.ts which
// attaches the JWT Bearer token. The backend's get_current_user dependency
// transparently falls through to a seeded dev user when DEV_MODE=true, so
// missing-auth bugs work locally — but production has DEV_MODE=false and
// correctly returns 401.
//
// This script greps src/ and fails if any file outside the allowlist calls
// fetch() against a /api/* path literal. Run via `npm run check:no-raw-fetch`
// and as a CI step.
//
// Allowlist:
// - src/lib/apiFetch.ts and src/composables/useApi.ts host the wrappers
//   themselves and necessarily call raw fetch().
// - src/stores/auth.ts is the auth bootstrap: /me manually constructs the
//   Bearer header (the wrapper would create a chicken-and-egg with the
//   token store), and /dev-login and /telegram are public endpoints.

import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, relative, resolve } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const root = resolve(dirname(__filename), '..')
const srcDir = resolve(root, 'src')

const ALLOWED = new Set([
  'src/lib/apiFetch.ts',
  'src/composables/useApi.ts',
  'src/stores/auth.ts',
])

const PATTERN = /\bfetch\(\s*[`'"]\/api\//

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name)
    if (entry.isDirectory()) yield* walk(p)
    else if (entry.isFile() && /\.(ts|vue|mjs)$/.test(entry.name)) yield p
  }
}

const violations = []
for (const abs of walk(srcDir)) {
  const rel = relative(root, abs).replaceAll('\\', '/')
  if (ALLOWED.has(rel)) continue
  const text = readFileSync(abs, 'utf8')
  text.split('\n').forEach((line, i) => {
    if (PATTERN.test(line)) {
      violations.push(`${rel}:${i + 1}: ${line.trim()}`)
    }
  })
}

if (violations.length > 0) {
  console.error('::error::Raw fetch() calls to /api/* found. Use apiFetch() from @/lib/apiFetch instead.')
  console.error('These calls bypass the JWT Bearer header injection and will return 401 in production:')
  for (const v of violations) console.error(`  ${v}`)
  process.exit(1)
}

console.log("OK: no raw fetch('/api/...') calls outside the allowlist.")
