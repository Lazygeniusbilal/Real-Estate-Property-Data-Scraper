---
description: Create a spec document grounded in goals.md and AGENTS.md
argument-hint: "step number and feature name, e.g. 2 scraper-transport"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are an AI agent creating a spec document for the Graana Market
Intelligence project. Follow all rules in @AGENTS.md.
Read @goals.md first — it is the source of truth for objectives,
deliverables, scope, schedule, and risks.

User input: $ARGUMENTS

Decisions already made for this project (do not re-ask, do not list
as open questions):
- Database: Supabase (user configures the project themselves).
- Frontend: Next.js + TypeScript + Tailwind via
  `npx create-next-app@latest frontend/`.
- Scraper: default transport is the structured JSON API
  (`/search/listings`, `/_next/data/.../property/<slug>.json`);
  HTML path-page fallback exists for resilience.

## Step 0 — Check working directory is clean

Run `git status`. If there are uncommitted, unstaged, or untracked
files, stop immediately and warn the user:

> "The working directory has uncommitted changes. Please commit or
> stash them before creating a spec."

Do not continue until the working directory is clean.

## Step 1 — Determine the spec topic

From $ARGUMENTS extract:
1. `step_number` — zero-padded to 2 digits: 2 → 02, 11 → 11.
   This maps to the day/milestone structure in goals.md.
2. `feature_name` — human-readable feature name, converted to a
   kebab-case slug (lowercase, a–z, 0–9, dashes, max 40 chars).

- If either is missing or ambiguous, ask the user to clarify.
- Cross-check the step against goals.md so the spec ties to a real
  schedule item; if the requested step is already marked done in
  goals.md, warn the user before proceeding.
- Derive the output filename as
  `.opencode/specs/<step_number>-<feature_slug>.md`.

## Step 2 — Ask before writing

Ask the user to confirm:
- The spec's scope boundaries (what is explicitly out of scope).
- Any constraints specific to this feature.
- The output filename (suggest `.opencode/specs/<step_number>-<feature_slug>.md`).

## Step 3 — Write the spec

Generate a spec with this structure:

---
# Spec: <Topic>

## Overview
One paragraph: what this covers and why, tied to goals.md.

## Objectives
Bulleted goals, derived from goals.md only.

## Deliverables
Concrete outputs (files, endpoints, tables, models, pages).

## Scope
- In scope: ...
- Out of scope: ... (cross-check against goals.md MVP vs. stretch)

## Requirements
### Functional
### Non-functional

## Constraints
- Follow AGENTS.md conventions (uv, type hints, no PII, etc.)
- Do not exceed the scope defined in goals.md.

## Open Questions
Anything unresolved. List, never guess. Remaining typical candidates:
- Frontend page layout/routes
- Model evaluation targets (specific MAE/MAPE/R² thresholds)
- Render API deployment details
---

Rules for content:
- Ground every claim in goals.md, AGENTS.md, or the codebase.
- Do not invent details (endpoints, schemas, pages) not already implied.
- Do not expand scope beyond goals.md.
- If a decision is unresolved, put it in Open Questions.

## Step 4 — Save and report

Save to `.opencode/specs/<step_number>-<feature_slug>.md`
(create the directory if needed).
Report the path and title. Do not print the full spec unless asked.
