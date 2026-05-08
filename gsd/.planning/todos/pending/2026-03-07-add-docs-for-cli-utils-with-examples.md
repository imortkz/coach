---
created: 2026-03-07T16:40:48.449Z
title: Add docs for CLI utils with examples
area: docs
files: []
---

## Problem

The scripts/ repo contains CLI utilities (migrations, seed, analytics) but lacks user-facing documentation with usage examples. New users or future-self won't know available commands, flags, or expected output without reading source code.

## Solution

Create a docs section (README or dedicated docs/) in scripts/ covering each CLI entry point with example invocations and expected output. Consider including: migrate, seed, export, import, and analytics commands.
