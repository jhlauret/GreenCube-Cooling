# Geolocation contract and cache policy (GC-COOLING-03)

This documents the actual, shipped implementation — not the aspirational
architecture in `GC_COOLING_PROMPTS/README_GC-COOLING-03_GEOLOCATION.md`
(that document describes a much larger multi-provider service; see
"Décisions d'architecture / scope réduit" below for what was and was not
built from it in this pass).

## 1. What this covers

- Address search and coordinate-based altitude/timezone lookup
  (`services/geo.py`, backed by the free Open-Meteo APIs — no API key).
- A lookup cache (`models/geo_cache.py`, `greencube.cooling.geo.cache`).
- Storage of the resolved location on `greencube.cooling.study` itself
  (`address`, `city`, `zip`, `country_id`, `latitude`, `longitude`,
  `altitude_m`, `timezone`, `environment_type`) plus its provenance/audit
  fields (`location_provenance`, `location_precision`, `location_provider`,
  `location_resolved_at`, `location_source_json`).
- `action_confirm_geolocation()` / `POST /studies/{id}/confirm-location`,
  the only path allowed to mark a location `climate_confirmed`.

It does **not** cover climate history, percentiles, heatwave detection or
the solver — those are GC-COOLING-04/14/15's scope.

## 2. Décision d'architecture : pas de modèle `greencube.location` séparé

The prompt allows either introducing a `greencube.location` model or
documenting why the fields stay on the study for the MVP. This pass keeps
them on `greencube.cooling.study`:

- every current consumer (the API serializer, the frontend's
  `LocationData`, the MERCURE honeybee translator) already reads location
  data straight off the study; a 1:1 child model would only add a join
  everywhere for no behavioural gain at this cardinality (one location per
  study, never shared/reused across studies);
- a study's location genuinely is 1:1 with the study today — nothing in
  this module reuses a location across two studies;
- introducing a separate model now would touch `ir.model.access.csv`,
  record rules, the API serializer, the frontend sync layer and every test
  that creates a study, for a refactor with no functional payoff yet.

If a future lot needs to reuse a resolved location across several studies
(e.g. a customer's site catalogue), that is the trigger to extract
`greencube.location` — not before.

## 3. Enum alignment: `dense_urban`

`environment_type` is `rural | suburban | urban... ` — concretely:
`dense_urban, suburban, rural, mountain, coastal, industrial` (there is no
plain `urban`; `dense_urban` is the canonical "urban" value, matching both
`models/cooling_study.py` and `frontend/src/types/study.ts` /
`LocationStep.tsx` at the time of this pass). The historical audit finding
("frontend uses `urban_dense`, Odoo expects `dense_urban`") was already
fixed on both sides before this pass started; this pass adds:
- `migrations/18.0.6.0.0/post-migrate.py`, which normalizes any leftover
  `urban_dense` row (from an older, unaligned build) to `dense_urban` via
  raw SQL — see that file's docstring for why raw SQL, not the ORM;
- `tests/test_geolocation.py::TestEnvironmentEnumMigration`, which forces a
  row back into the legacy state via SQL and runs the actual migration
  script against it.

## 4. Latitude/longitude/altitude/timezone validation

Enforced in two independent places (defense in depth, both real, neither a
rubber stamp for the other):

- `controllers/api.py`'s `_range_error()` / `services/api_validation.py`
  (`FIELD_LIMITS`) — used by `PATCH /studies/{id}`,
  `GET /geo-context` and `POST /studies/{id}/confirm-location`.
- `models/cooling_study.py::_check_location_bounds` — an
  `@api.constrains` on `latitude, longitude, altitude_m, timezone`, so any
  write path that bypasses the HTTP controller (demo data, another
  module, `odoo shell`) is still bounded.

Bounds: latitude `[-90, 90]`, longitude `[-180, 180]`, altitude
`[-500, 9000]` m. Timezone must be a real IANA zone name (validated
against Python's `zoneinfo.available_timezones()`) — a bare UTC offset
(`"UTC+02:00"`) is rejected, matching README §13 "ne jamais retourner
uniquement un offset UTC".

**Zero is a real coordinate.** `latitude`/`longitude` are Odoo `Float`
fields, which cannot distinguish "never set" (defaults to `0.0`) from a
genuine equator/Greenwich-meridian location. Every presence check in this
module therefore uses `climate_confirmed` (a real boolean, set exclusively
by `action_confirm_geolocation()`), never `bool(latitude)` /
`latitude != None` where `None` can't occur —
`_missing_required_sections()`, `get_validation()`, and the API's
`_serialize_study()` all follow this rule; see the comments at each site.
On the frontend, `study.location.latitude != null` is used instead
(TypeScript `number | null`, so `0` is correctly truthy-safe there).

## 5. Provenance and precision

`location_provenance` — how the currently-stored coordinates were
obtained:
- `manual` (default) — typed/corrected by the user directly;
- `geocoded` — from an address search result;
- `browser` — from the browser's Geolocation API (still revalidated
  server-side and never trusted for altitude, per README §2.4);
- `imported` — reserved for a future bulk-import path; not used by any
  current caller.

`location_precision` — coarseness of the coordinates: `exact | locality |
region | country | unknown`.

`location_provider` — the name of the service that produced the values
(e.g. `open-meteo`), or empty for a manual entry.

`location_resolved_at` — when the value currently stored was confirmed.

`location_source_json` — a **minimal**, whitelisted subset of the
provider's response (`display_name`, `city`, `country_code`,
`confidence_percent`) kept for audit. The raw provider payload and the
full free-text address are never stored here and never logged (see §7).

A manual correction after a geocoded confirmation **overwrites**
provenance/precision — it is not blended with the previous value, since
provenance describes how the value currently on the record was obtained,
not its full history (tracking is still available via `mail.thread`
(`tracking=True` on `location_provenance`), which does keep the full
change log).

## 6. `action_confirm_geolocation()` / `POST /confirm-location`

A plain `PATCH /studies/{id}` can still write raw `latitude`/`longitude`
(e.g. to clear a location, or for a script), but never sets
`climate_confirmed`, provenance, precision or the resolved timestamp.
`POST /studies/{id}/confirm-location` is the only path that does, and it:

1. re-validates the payload server-side (never trusts a client-supplied
   `climate_confirmed=true` from a raw PATCH as "the user actually
   confirmed a real location" — only this endpoint carries that meaning);
2. records provenance/provider/precision/resolved_at;
3. stores the minimal source snippet;
4. sets `climate_confirmed = True`;
5. invalidates any frozen calculation snapshot
   (`_invalidate_active_snapshot()`), so a stale MERCURE run is never
   silently kept after the location changes;
6. goes through the model's normal `write()` override — confirming a new
   location on a `validated` study still raises "create a revision"
   (`COOLING_STUDY_LOCKED`, HTTP 409) instead of mutating history in
   place. A `calculated` (but not yet `validated`) study is **not**
   locked, consistent with every other section-edit route in this module
   — the snapshot invalidation is what forces a fresh calculation, not a
   write-time block.

Rate-limited 10 confirmations/minute/study (`_check_rate_limit`), matching
README §17.

## 7. Logging / secrets

`controllers/api.py`'s `_guarded` decorator logs one line per request
(route, method, user id, company id, status, duration) and never the
request body — the full address is never written to the application log.
`location_source_json` deliberately keeps only a small whitelist of
fields, not the raw provider payload, for the same reason if it is ever
dumped for debugging.

## 8. Cache (`greencube.cooling.geo.cache`)

One row per `(kind, rounded coordinate pair, schema version)` for
`kind=context` lookups (altitude + timezone); address search
(`kind=search`) is not persisted beyond Open-Meteo's own layer, since
results legitimately change as new places get indexed — a decision already
made before this pass and left as is.

- **Key**: `context:{lat rounded to 5 decimals}:{lon rounded to 5
  decimals}:v{GEOLOCATION_SCHEMA_VERSION}` (README §8: 5 decimals ≈ 1.1 m).
  `GEOLOCATION_SCHEMA_VERSION` must be bumped whenever the cached payload
  shape changes incompatibly, so old rows are naturally bypassed instead
  of being misread.
- **TTL**: `greencube_cooling.geocoding_cache_ttl_days` (`ir.config_parameter`),
  default 90 days (README §6). Altitude/timezone for a coordinate almost
  never change, so a long TTL is safe.
- **Status**: `available | partial | stale | failed`.
  - `partial`: the provider answered but altitude or timezone was missing.
  - `stale`: the provider is currently unreachable and an expired cache
    entry was served back instead of failing outright (fallback tier,
    README §5.4 "cache ancien"). The caller can tell the difference
    (`status` is part of the cached payload's row, though not currently
    surfaced through `/geo-context`'s response body — see §10 limitations).
  - `failed`: reserved for a future explicit error-caching path; not
    currently written (a failed lookup with no cache to fall back to
    raises `GeoServiceError` straight to the controller, which returns
    502 `GEO_PROVIDER_UNAVAILABLE` — nothing is invented).
- **No Internet in tests**: every test that exercises the cache
  (`tests/test_geolocation.py::TestGeoCache`) monkeypatches
  `services.geo.get_geo_context`; none of this module's tests make a real
  network call.

## 9. Adding a provider

The current implementation is a single free provider (Open-Meteo) behind
`services/geo.py`, not the full pluggable `GeocodingProvider` /
`ElevationProvider` / `TimezoneProvider` abstraction sketched in the
detailed README (see §10). To add a second provider today: extend
`services/geo.py` with a second implementation function, branch on an
`ir.config_parameter` (e.g. `greencube_cooling.geocoding_provider`) inside
`search_address`/`get_geo_context`, and keep `models/geo_cache.py`'s public
methods' signatures unchanged so `controllers/api.py` needs no change.

## 10. Scope reduced from the detailed README — explicitly out of this pass

The long-form spec (`README_GC-COOLING-03_GEOLOCATION.md`) describes a
considerably larger service than what an "incremental, conservative patch"
on the existing, working `services/geo.py` + `geo_cache.py` justifies. The
following are **not** implemented and are documented here as a conscious,
bounded gap rather than silently dropped:

- A pluggable multi-provider registry (`provider_registry.py`,
  `nominatim_provider.py`, `mock_provider.py`, ...) — only Open-Meteo
  exists today, reachable via `services/geo.py`.
- A standalone, explainable environment classifier with a weighted
  confidence score and per-suggestion "reasons" (README §14/§15). The
  existing `environment_type` remains a plain user-selected enum with no
  auto-suggestion.
- A dedicated `greencube.location` model (see §2 above for the reasoning).
- A scheduled cache-cleanup cron (README §21) purging expired/unused rows.
  The table is small (one row per distinct rounded coordinate) and the
  existing TTL check already stops stale rows from being served as fresh;
  unbounded growth cleanup is left for a future pass if the table actually
  grows large in production.
- Structured observability counters (README §24: hit rate, per-provider
  error counts, etc.) beyond the `_guarded` request log line and the
  cache row's own `status`.
- A frontend UI for typing raw manual coordinates (only search-result
  selection and the browser's Geolocation API feed coordinates in today);
  the backend (`action_confirm_geolocation`, `POST /confirm-location`)
  already accepts an arbitrary `provenance: "manual"` payload, so this is
  a frontend-only gap, not a contract limitation.

None of these gaps block the acceptance criteria this pass does cover
(zero-coordinate handling, enum alignment + migration, bounds/timezone
validation, cache hit/miss/stale-fallback, provenance/precision/audit
trail, confirmation locking the study, cross-user access denial).
