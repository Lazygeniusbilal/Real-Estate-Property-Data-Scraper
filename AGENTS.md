# AGENTS.md

Instructions for AI agents working in this repository.

## Project overview

We are building **Graana Market Intelligence** — an end-to-end data product on top of
graana.com (Pakistan's largest property portal). An automated pipeline ingests every
active property listing across Pakistan, cleans and stores it, computes market analytics
(price-per-sqft, rental yields, area scorecards), trains a fair-value price model, and
serves a geospatial dashboard with an investment screener and an AI search layer.

Full goals, scope, architecture, and schedule: **see `goals.md` (source of truth).**

## Objectives and deliverables

Must deliver (MVP):
- All-city scraper for graana.com (listings + detail enrichment), with retries and a
  swappable transport. **Default to the site's structured JSON API; fall back to HTML
  scraping only if no JSON endpoint is available.** Confirmed JSON endpoints:
  - Listings: `GET https://www.graana.com/search/listings?cityId=<id>&purpose=<buy|rent>&type=<residential|commercial>&page=<n>`
    → 30 per page plus a `count` total.
  - Detail: `GET https://www.graana.com/_next/data/<buildId>/property/<slug>.json`
    → object at `pageProps.data`.
- Clean normalized data in **Supabase** (plus Parquet/DuckDB for bulk analytics), no PII.
- Analytics marts: price-per-sqft, rental yield, area scorecards, city/subtype aggregates.
- A LightGBM fair-value price model with SHAP explanations.
- FastAPI backend deployed on Render.
- Next.js + TypeScript + Tailwind dashboard deployed on Vercel. The frontend is a single
  (monolithic) Next.js app in a `frontend/` directory, scaffolded with
  `npx create-next-app@latest frontend`. The FastAPI backend remains a separate service.
- README with architecture, setup, and data dictionary.

Out of scope:
- Image models, forecasting, and fraud detection.
- Time-series UI (only one snapshot fits the schedule).
- PII such as agent names, phones, and emails (agency business name for aggregates is fine).
- The original first-3-cities-only, 2-page scope of the legacy `main.py`.

Stretch (only if the MVP is done):
- LLM natural-language search, monthly change-tracking, recommendation engine,
  deeper projects module, anomaly detection, Wayback-Machine historical backfill.

## Tech stack

- Python for scraping, the pipeline, and ML.
- **Dependencies and virtual environments are managed with `uv`** (not pip).
- Existing runtime deps in `requirements.txt`: pandas, numpy, requests, beautifulsoup4 (bs4).
- Planned additions (see `goals.md`): polars, pydantic, tenacity, LightGBM, SHAP, FastAPI,
  DuckDB, pytest, and a Supabase/Postgres client.
- Frontend (planned): Next.js + TypeScript + Tailwind on Vercel.

## Commands

Backend uses `uv`. This project is migrating from pip to uv; until a `pyproject.toml` /
`uv.lock` exists, use the requirements file, then prefer `uv sync` / `uv run`.

Backend:
- Install (current): `uv pip install -r requirements.txt`
- Install (after uv migration): `uv sync`
- Run the current scraper: `uv run python main.py`
- Unit tests: `uv run pytest` (only once tests exist)

Frontend (Next.js + TypeScript + Tailwind — run from the `frontend/` directory):
- Scaffold (only if starting fresh): `npx create-next-app@latest frontend`
- Install: `npm install`
- Dev server: `npm run dev`
- Production build: `npm run build`
- Run built app: `npm start`
- Lint: `npm run lint`

Do not assume test, lint, or build tooling exists before it is actually set up.

## Testing and workflow

- **Unit tests:** every feature gets unit tests before commit.
- **Smoke test:** run a smoke test as well before committing.
- **Integration tests:** run in GitHub Actions once features are shipped.
- Work in small, focused steps aligned with the deliverables above.
- Keep changes scoped to the current step; avoid unrelated edits.
- Ask the user before large changes, such as adding dependencies, restructuring files,
  or changing the architecture in `goals.md`.

## Code style and conventions

- Follow PEP 8; use clear, descriptive names.
- Use type hints for functions where practical.
- Keep dependencies to what `goals.md` calls for.
- Match the existing style in `main.py` (straightforward, readable scripting) unless a
  clear reason to improve it arises.
- Do not add PII to data structures or outputs.

