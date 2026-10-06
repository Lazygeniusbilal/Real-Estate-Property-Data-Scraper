# Spec: Scaffolding

## Overview

Day 1 of the goals.md schedule ("Scaffolding") establishes
the project skeleton: a uv-managed Python backend layout and a create-next-app
frontend. This spec covers only the scaffolding half of Day 1 — repo structure
and dependency management. Scraper implementation, config, pipeline modules, and
all later-day work are out of scope.

## Objectives

- Establish a clean Python project layout ready for future modules.
- Migrate dependency management from `requirements.txt` to `pyproject.toml` /
  `uv.lock` (`uv sync` / `uv run`), per AGENTS.md.
- Scaffold the frontend with `npx create-next-app@latest frontend/`
  (Next.js + TypeScript + Tailwind).

## Deliverables

- `pyproject.toml` + `uv.lock` (with existing deps from `requirements.txt`:
  pandas, numpy, requests, beautifulsoup4 — plus planned additions listed in
  AGENTS.md/goals.md, added only as needed in this step).
- New backend package layout (empty package skeleton only).
- `frontend/` created via `npx create-next-app@latest frontend/`.
- Updated `.gitignore` (e.g., `myvenv`, `data/`, `frontend/node_modules`,
  `.next`).
- README section update describing the new layout (full README is a Day 7
  deliverable).

## Scope

- In scope:
  - Repo restructure and package layout (backend + `frontend/`).
  - uv migration (`pyproject.toml`, `uv.lock`).
- Out of scope:
  - Typed config for cities.
  - Scraper implementation of any kind (threaded fetcher, retries/backoff,
    transports, dedup, logging, kicking off the ~1–2h scrape).
  - Transform, analytics marts, ML model, FastAPI endpoints, Supabase schema.
  - Stretch items (LLM search, change-tracking, projects module, etc.).

## Requirements

### Functional

- `uv sync` / `uv run` must work in a fresh checkout.
- Frontend scaffold builds (`npm run build`) and lints (`npm run lint`) cleanly.

### Non-functional

- No PII anywhere in the skeleton.
- Type hints on public functions (PEP 8, per AGENTS.md).
- No new runtime dependencies beyond those listed in goals.md/AGENTS.md.
- Legacy `main.py` either retained or cleanly superseded by the new layout.

## Constraints

- Follow AGENTS.md conventions (uv, type hints, no PII, small scoped steps).
- Do not exceed goals.md scope; skeleton layout only (this step).
- Database remains Supabase (user configures the project); no schema work in
  this step.

## Open Questions

- Whether planned deps beyond `requirements.txt` (polars, pydantic, tenacity,
  etc.) should be added in this step or as each module lands.

## Resolved Decisions

- Backend layout: uv standard `src/` layout with package `src/graana/`
  (user wrote "granna" — confirm spelling before implementation).
- Legacy `main.py` is kept as-is until the project is complete; `requirements.txt`
  is kept alongside uv until all modules land, then deleted.
