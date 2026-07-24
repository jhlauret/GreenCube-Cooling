# Climate service contract, provenance and scope (GC-COOLING-04)

This documents the actual, shipped implementation — not the aspirational
20-class architecture in
`GC_COOLING_PROMPTS/README_GC-COOLING-04_SERVICE_CLIMATIQUE_COMPLET.md`
(that document describes a full climate-data platform: provider registry,
async job pipeline, hourly QC, heat-sequence detection, recent-signal
analysis, EPW/weather-morphing, etc.). See "Scope réduit" below for what
was and was not built from it in this pass, and why.

## 1. What this covers

- `services/climate.py`: fetches ~10 years of daily historical weather
  (Open-Meteo archive API, ERA5 reanalysis, no API key) for a study's
  confirmed coordinates and derives three named dimensioning scenarios
  from real percentiles of the warm-season record:
  - `reference_summer` — P90 of warm-season daily max
  - `hot_weather` — P98 of warm-season daily max
  - `prolonged_heatwave` — the single hottest observed warm-season day
- `models/climate_dataset.py` (`greencube.cooling.climate.dataset`): an
  immutable, versioned cache of that fetch, keyed by
  `(lat, lon, environment_type, provider_code, provider_version,
  schema_version)`.
- `models/climate_scenario.py` (`greencube.cooling.climate.scenario`): the
  last-computed scenario values for a study, denormalized from the
  dataset above (or from the altitude-based fallback heuristic when no
  historical fetch succeeded), exposed to the API with full provenance.
- `cooling_study.py::_build_climate_scenarios()` — called from
  `action_calculate()`/`action_create_snapshot()`, never from a plain
  read — feeds these scenarios straight into the frozen MERCURE
  snapshot payload (`input_snapshot_json`), so a validated calculation's
  climate inputs are byte-for-byte reproducible regardless of what the
  live cache later does.

## 2. Dataset types and honest labeling

`greencube.cooling.climate.dataset.dataset_type` distinguishes:

| Value | Meaning | Produced today? |
|---|---|---|
| `historical_observed` | Real observed daily weather (ERA5 reanalysis) | **Yes** — the only type this service ever produces |
| `typical_year` | A synthetic "typical meteorological year" | No |
| `design_day` | A single engineered design day | No |
| `extreme_event` | A specific selected historical extreme | No (the three named scenarios are percentile-based, not event-matched) |
| `projection` | A forward-looking climate-model scenario (e.g. CMIP6/CORDEX) | **No — reserved.** This service has no prospective-model provider. |

**Audit finding fixed by this pass**: the Location step's UI badge used to
read "Projections climatiques" ("climate projections") next to a list of
historical-data facts, which falsely implied a forward-looking climate
model was in play. It has been corrected to "Historique multi-année (10
ans)" (`frontend/src/routes/steps/LocationStep.tsx`). Nothing in the
backend or frontend may claim `projection` without also wiring a real
prospective-model provider behind its own feature flag — see
`services/climate.py`'s `DATASET_TYPE_HISTORICAL_OBSERVED` docstring.

## 3. Provenance / governance fields

Every dataset row carries: `dataset_type`, `provider_code`
(`open_meteo`), `provider_version` (`archive_v1`), `schema_version` (`1`),
`license`, `timezone` (the IANA zone Open-Meteo itself resolved for
`timezone=auto`), `variables` (the exact provider variable codes
requested), `checksum` (SHA-256 of the serialized payload), `fetched_at`/
`fetched_epoch`, `data_start`/`data_end`, `sample_days`.

`provider_version`/`schema_version` bump whenever the request shape, the
variable list, or the returned payload shape changes — both are folded
into the cache key, so a version bump always produces a **new** dataset
row instead of silently reinterpreting an old cached row under a new
meaning (README §"Immuabilité et versionnement" /
"changement de fournisseur ou version créant un nouveau dataset, pas une
mutation silencieuse").

`greencube.cooling.climate.scenario` denormalizes `dataset_id`,
`dataset_type` and `checksum` from the dataset it was derived from, so
the API (`GET /studies/{id}` → `location.climate_scenarios[]`) can expose
full provenance without a join and without ever handing the frontend a
provider URL, API key, or raw provider payload.

## 4. Immutability and cache refresh

`climate.dataset.get_or_fetch_scenarios()` **never** calls `write()` on
an existing dataset's data fields. When the 90-day cache TTL has expired
(or the cache key doesn't exist yet), it:
1. fetches fresh data and `create()`s a brand-new dataset row with its
   own checksum;
2. if an old row existed for that key, archives it
   (`active=False`, `superseded_by_id=<new id>`) — the old row's payload,
   checksum and every field a snapshot may have already captured stay
   exactly as they were.

This means a dataset that has already fed a frozen `input_snapshot_json`
(via `action_create_snapshot()`) is safe from any later refresh of the
live cache — the old row keeps existing (soft-archived, not deleted) and
its content never changes.

## 5. Reproducibility

Given the same provider response, `build_climate_scenarios()` is
deterministic (fixed percentile method, no randomness, no wall-clock
dependence beyond "which years are in the lookback window"), so the same
input always produces the same `payload_json` and therefore the same
SHA-256 checksum — this is asserted directly by
`tests/test_climate_service.py::test_reproducible_checksum_for_same_input`.

## 6. Failure handling

`ClimateServiceError` is raised (never a silent empty/zero result) on:
network failure, non-2xx response, malformed/empty response, or fewer
than 30 warm-season samples for the location. `cooling_study.py` catches
it and falls back to `_climate_scenarios_from_heuristic()` (a
conservative altitude-based estimate), logging a warning and marking
those scenario rows with `provenance='estimated_reference'` and no
`dataset_id`/`dataset_type` — so a caller can always tell "this came from
real history" from "this is the safety-net heuristic" instead of the two
being silently indistinguishable.

## 7. Scope réduit — ce qui n'a PAS été construit dans cette passe

The full README describes an entire climate-data platform. The following
were deliberately **not** built, as concrete, conservative fixes to the
audit's actual findings (frontend false claim, missing governance
fields, mutable cache, no provenance exposure) were judged to be the
real, verifiable gap — not a from-scratch platform:

- **Provider registry / multiple providers** (`ClimateProviderRegistry`,
  Meteostat, ERA5-Land, Météo-France, MeteoSwiss, EPW file import). Only
  Open-Meteo exists today; the frontend never selects a provider (already
  true before this pass) and provider governance fields
  (`provider_code`/`provider_version`) are in place so adding a second
  provider later is additive, not a breaking change.
- **Async job pipeline for climate fetch** (`queued` → `fetching` → ... →
  `completed`). The Open-Meteo archive call this service makes typically
  completes in 1-3 seconds; it runs synchronously inside
  `action_calculate()`/`action_create_snapshot()`, which is itself already
  a direct HTTP request-response call for the `quick_solver` engine (see
  GC-COOLING-16 for the actual async job model, which governs the
  EnergyPlus path where a real long-running job is unavoidable). If a
  future provider is genuinely slow, that provider integration should go
  through the existing `calculation.job` machinery rather than adding a
  second bespoke job system just for climate.
- **Hourly observations, quality-control flags, percentile engine over
  raw hourly data, cooling-degree-hour/hot-night/heat-sequence detectors,
  recent-climate-signal analyzer, weather morphing, EPW ingestion.** The
  shipped service only ever needs **daily** aggregates (max/min/mean
  temperature, mean humidity, radiation sum, max wind) to compute the
  three percentile-based scenarios MERCURE actually consumes; building an
  hourly QC/statistics engine with no current consumer would be dead code
  by this campaign's own conservative-patch rule.
- **Canonical `greencube.cooling.climate.event` model.** No feature in
  this codebase selects "the worst 5-day heatwave in the last 10 years"
  today — `prolonged_heatwave` is the single hottest *day*, not a
  detected multi-day event. Introducing the event model without any
  detector or consumer would be speculative scaffolding; the selection
  method that *is* implemented (percentile of daily max) is documented
  here instead (§1).
- **Dedicated UI for climate provenance/history.** The README's own flow
  diagram lists GC-COOLING-07 ("écran Localisation et contexte
  climatique") as the downstream consumer of this service. This pass
  only fixes the false "Projections climatiques" claim already visible
  today and exposes the provenance/dataset_type/checksum fields via the
  API (`location.climate_scenarios[]`) for GC-COOLING-07 to build a
  richer screen against later.
- **SSRF domain allowlist / DNS pinning middleware.** `services/climate.py`
  calls a single hardcoded constant URL (`ARCHIVE_URL`); there is no code
  path, request parameter, or user input anywhere that can influence which
  host is contacted, so there is no attacker-controlled URL to defend
  against yet. This must be revisited the moment a second, user- or
  admin-configurable provider is introduced.

## 8. Tests

`tests/test_climate_service.py` — pure-Python (no ORM), following the
`test_mercure_engine.py` pattern: mocks `requests.get`/
`climate_service.fetch_historical_daily` to test parsing, unit handling,
percentile selection, and reproducibility without any network access.

`tests/test_climate_dataset.py` — `TransactionCase`: cache hit/miss,
TTL expiry triggering a new dataset row + archiving the old one
(`active=False`, `superseded_by_id`), and that a provider/schema version
bump also forces a new dataset row.
