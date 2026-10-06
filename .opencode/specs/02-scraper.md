# Spec: Scraper

## Overview

Day 2 of the goals.md schedule ("Scraper") builds the ingestion layer of Graana
Market Intelligence: a threaded, retrying scraper that covers all 78 cities
across buy/rent and residential/commercial, with a swappable transport (JSON API
by default, path-page HTML fallback for resilience). It writes immutable, dated
raw output so the rest of the pipeline (transform, storage, analytics, ML, API,
dashboard) can be built on a real all-Pakistan snapshot. This spec covers the
raw scrape only; normalization, validation, and everything downstream are later
steps.

## Objectives

- Ingest every active listing across all 78 cities (not just the big three), per
  goals.md scope.
- Use the site's structured JSON API as the default transport, with a path-page
  HTML fallback for resilience.
- Enrich listings with detail data so the raw snapshot contains the fields later
  steps need.
- Produce raw, immutable, dated output before any cleaning (cache raw first, per
  goals.md risk mitigation).
- Kick off the full all-cities scrape (~1–2h) in the background.

## Deliverables

- Typed config for all 78 cities (and the buy/rent × residential/commercial
  matrix), added as a module in `src/graana/`.
- Threaded scraper with retries/backoff (`tenacity`), a real User-Agent,
  rate-limiting, dedup, and logging.
- Swappable transport interface:
  - Transport A (default): `GET https://www.graana.com/search/listings?cityId=<id>&purpose=<buy|rent>&type=<residential|commercial>&page=<n>`
    (30 per page plus a `count` total).
  - Transport B (fallback): path-based HTML pages.
- Detail enrichment: `GET https://www.graana.com/_next/data/<buildId>/property/<slug>.json`
  (object at `pageProps.data`).
- Raw dated output under `data/raw/YYYY-MM-DD/` as immutable Parquet + JSON.
- Dedup and run logging.
- The full all-cities scrape running in the background.

## Scope

- In scope:
  - Typed city/purpose/type config covering all 78 cities.
  - Paginated list fetching with a swappable transport (JSON default, HTML
    fallback).
  - Detail enrichment per listing.
  - Retries, backoff, real UA, rate-limiting, dedup, logging.
  - Raw dated Parquet + JSON output.
  - Kicking off the full scrape.
- Out of scope:
  - Normalizing units (marla/kanal/sqft → sqft), parsing prices, or any
    cleaning/validation (Day 3).
  - PII handling beyond simply not collecting agent names/phones/emails (PII is
    out of scope project-wide; agency business name only for aggregates).
  - Postgres/Supabase load, data dictionary, EDA (Day 3).
  - Analytics marts, ML features/model, FastAPI endpoints, frontend (Days 4–6).
  - All stretch items (LLM search, change-tracking, projects module, anomaly
    detection, Wayback backfill).
  - Image download/modeling; only listing metadata needed downstream.

## Requirements

### Functional

- Enumerate every city and iterate each `{buy, rent} × {residential, commercial}`
  combination, paginating until the `count` total is reached.
- Default to the JSON API transport; use the HTML path-page fallback when the
  JSON transport is unavailable or fails.
- Enrich each listing via the detail JSON endpoint, extracting from
  `pageProps.data`.
- Retry failed requests with exponential backoff (tenacity).
- Deduplicate listings within a run (by listing identity from the source).
- Write immutable dated Parquet + JSON to `data/raw/YYYY-MM-DD/`.
- Log progress and failures so the background run is auditable.
- Support running the full loop in the background for the ~1–2h scrape.
- Load the canonical 78-city list and `cityId` values from a committed data file
  (`cities.yaml` or `cities.json`) via the typed config (Pydantic,
  `extra="forbid"`); never discover cities at runtime.
- Fetch the Next.js `buildId` at the start of each run from the site's embedded
  HTML; never hardcode it.
- On a 404 from a detail request, refresh the `buildId` exactly once and retry
  that request.
- Write one Parquet file per city (`data/raw/YYYY-MM-DD/<city>.parquet`) with the
  as-scraped listing fields plus `scraped_at` and `source`, retaining the full raw
  detail JSON in a separate column or file.
- When the HTML fallback is used, return only the core fields (`id`, `price`,
  `area`, `location`, `type`, `bedrooms`) and set all other fields to `null`.

### Non-functional

- Low request volume, real User-Agent, and rate-limiting to reduce
  anti-bot/blocking risk (goals.md risk table).
- Raw output cached before any processing so a blocked/partial run is
  recoverable.
- No PII stored.
- Type hints on public functions; PEP 8, per AGENTS.md.
- Dependencies limited to those called for in goals.md/AGENTS.md (e.g.
  `requests`, `tenacity`, `polars`/`pandas` for Parquet).

### Decisions

1. City list and `cityId` values
   - The canonical 78-city list and their `cityId` values are hardcoded in a
     committed data file (`cities.yaml` or `cities.json`) and loaded through the
     typed config (Pydantic, `extra="forbid"`).
   - Cities are never discovered from the site at runtime.
   - The file may be produced by a one-time discovery script; the generated file
     is committed, and the script is not part of the runtime path.
2. Next.js `buildId`
   - The `buildId` is fetched at the start of each scrape run from the site's
     HTML (it is embedded in the page).
   - If a detail request returns 404, the `buildId` is re-fetched exactly once
     and that request is retried.
   - The `buildId` is never hardcoded.
3. Raw schema and file layout
   - Output folder is `data/raw/YYYY-MM-DD/`, one folder per scrape run, never
     overwritten.
   - One Parquet file per city: `data/raw/YYYY-MM-DD/<city>.parquet`.
   - Columns are the listing fields as-scraped, plus `scraped_at` and `source`.
   - The full raw detail JSON is retained in a separate column or file so nothing
     is lost.
   - Exact columns are decided after inspecting one real response and then
     documented in this spec.
4. Rate limit, concurrency, User-Agent
   - Start conservative: 2–5 requests/sec and 4–8 threads.
   - Use an honest UA string, e.g.
     `graana-research-bot/0.1 (contact: <email>)`.
   - All three (rate limit, concurrency, UA) live in config, not code; raise them
     only if the site tolerates it.
5. HTML fallback coverage
   - The fallback returns a reduced subset only: `id`, `price`, `area`,
     `location`, `type`, `bedrooms`.
   - All other fields are `null`.
   - The fallback exists only to keep the scrape alive if the JSON transport
     breaks.

## Constraints

- Follow AGENTS.md conventions: uv-managed dependencies (`uv sync` / `uv run`),
  type hints, no PII, small scoped steps.
- Do not exceed goals.md scope — this step stops at raw dated output; no
  transform, storage, analytics, ML, API, or frontend work.
- Database is Supabase (user configures the project); no DB work in this step.
- The legacy `main.py` scraper is superseded by this work but is retained until
  the project is complete (per the scaffolding spec).
- JSON API is the confirmed default transport; HTML fallback exists for
  resilience. Respect the robots.txt reality (`Disallow: /*?`) knowingly, as
  noted in goals.md: low volume, real UA, cache raw, no PII.

## Acceptance Criteria

- The scrape loads all 78 cities and their `cityId` values from the committed
  data file; no runtime city discovery occurs.
- The `buildId` is fetched at run start; no `buildId` appears hardcoded in code.
- A 404 on a detail request triggers exactly one `buildId` refresh and a retry of
  that request.
- Output is written to `data/raw/YYYY-MM-DD/`, one folder per scrape run, never
  overwritten, with one `<city>.parquet` per city.
- Each Parquet file contains the as-scraped listing fields plus `scraped_at` and
  `source`, and the full raw detail JSON is retained in a separate column or file.
- The HTML fallback returns the core fields (`id`, `price`, `area`, `location`,
  `type`, `bedrooms`) and `null` for all other fields.
- Rate limit, concurrency, and UA are read from config (not code) with the
  conservative starting values (2–5 requests/sec, 4–8 threads, honest UA).
- The full all-cities scrape completes and produces the expected ~18.8k listings
  plus details.
