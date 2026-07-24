# Migration policy — greencube_cooling

Required by GC-COOLING-01 §10 ("toute modification de schéma doit disposer
d'une stratégie de migration"). This module had accumulated several
sessions of additive schema changes (new models, new fields) without ever
bumping `version` in `__manifest__.py` or creating this directory — that
gap is what this fixes.

## When a migration script is actually needed here

Odoo's ORM auto-creates new tables and new columns on `-u` upgrade
(`_auto_init`), so most additive changes in this module's history need
**no script**:
- Brand-new models (`calculation.snapshot`, `calculation.job`,
  `simulation.artifact`, `geo.cache`, `climate.dataset`, ...): Odoo creates
  the table; there is no prior data to reconcile.
- New optional fields with a default that is equally valid for old and new
  rows (e.g. a new `Char`/`Boolean` field defaulting to `False`/`""`):
  the ORM's own backfill is correct.

A script **is** needed when a new field's default is only correct for
*new* rows and would silently change the meaning of *existing* rows if
left at that default — see `18.0.2.0.0/post-migrate.py` for a concrete
case: `maximum_acceptable_temperature_c` replaced an inline
`cooling_setpoint_c + 2` computation, so pre-existing studies must be
backfilled with that same formula, not the new field's flat default.

The same rule applies to any future field/column rename (`pre-migrate.py`,
since the old column must still exist to copy from) or any change that
alters the *meaning* of previously-stored values.

## Bumping the version

Every session that changes `models/*.py` in a way covered by the rule
above must:
1. Bump `version` in `__manifest__.py` (the third digit, `18.0.X.0.0`, for
   additive/data-migrating changes; the fourth for pure bugfixes with no
   schema impact).
2. Add `migrations/<new-version>/{pre,post}-migrate.py` if — and only if —
   the rule above applies.

## 18.0.6.0.0 (GC-COOLING-03)

Adds `location_provenance`, `location_precision`, `location_provider`,
`location_resolved_at`, `location_source_json` to `greencube.cooling.study`
(new optional fields, ORM auto-backfill is correct — no script needed for
those) and normalizes any legacy `environment_type = 'urban_dense'` row to
`'dense_urban'` via `18.0.6.0.0/post-migrate.py` (raw SQL, see that file's
docstring for why the ORM is not used).

## 18.0.6.0.1 (GC-COOLING-13)

Pure bugfix, no schema impact, no migration script:

- `_build_mercure_input()` used to embed the study's *previous* snapshot
  hash (`self.input_snapshot_hash`) into the payload it builds for the
  *next* snapshot. Since that payload is itself what gets hashed to produce
  the new snapshot's hash, every call produced a different hash even when
  nothing about the study had actually changed — silently defeating the
  idempotence `action_create_snapshot()`/`POST .../snapshots` is required
  to have (a double click, a network retry, or a stale resubmit must not
  freeze a second, functionally-identical snapshot). Fixed to always embed
  `""` (the field is inherently unknowable before the payload is fully
  built and hashed) and `action_create_snapshot()` now short-circuits as a
  no-op when the currently active snapshot's hash already matches.
- `action_mark_ready()` now gates on `get_validation()`'s blocking rules
  (already the source of truth for `action_create_snapshot()` and the
  `/validation` route) instead of the narrower, separately-maintained
  `_missing_required_sections()` — e.g. a missing active solver version now
  blocks `ready` too, not only snapshot creation. `_missing_required_sections()`
  itself is unchanged and still used by `confirm_location()`'s completeness
  check and covered directly by `tests/test_geolocation.py`.

No existing stored data changes meaning: past `frozen`/`superseded`
snapshot rows keep whatever hash they were created with (they are
immutable by design, see `cooling_calculation_snapshot.py`'s `write()`
override) — only snapshots created *after* this upgrade get the corrected,
truly content-derived hash.

## 18.0.9.0.0 (GC-COOLING-12)

Adds `wind_exposure` (Selection, default `"normal"`, required) to
`greencube.cooling.ventilation.profile` — new optional-with-default field,
ORM auto-backfill is correct, no script needed.

No column is renamed or removed. `infiltration_ach` and `airtightness_n50`
on `greencube.cooling.ventilation.profile`, and `airtightness_n50` /
`default_infiltration_ach` on `greencube.thermal.specification`, all keep
their existing stored values and meaning as manual/fallback inputs.

What *does* change is which of those already-stored values the solver
actually reads, via the new `get_effective_infiltration_ach()` on
`greencube.cooling.ventilation.profile` (single documented n50->ACH
conversion, `ach_from_n50()` in `services/mercure/conversions.py`, plus a
documented additive increment from `door_opening_frequency` /
`window_opening_frequency`, both of which were previously stored,
exposed via the API and completely ignored by the solver):

- If a ventilation profile row already has `airtightness_n50 > 0` **and**
  `door_opening_frequency`/`window_opening_frequency` at their default
  `"occasional"` value (true for every pre-existing row, since neither
  field was ever settable from the UI before this release), a study
  recalculated after this upgrade will show a slightly different
  infiltration/ventilation contribution than before: the n50-derived ACH
  now wins over whatever was in `infiltration_ach`, and the default
  `"occasional"`/`"occasional"` pair now adds +0.06 ACH that used to add
  nothing. This is the intended fix (previously-ignored, already-entered
  data now actually affects the result) and is called out explicitly in
  Review/Results per the "toute donnée non utilisée doit être signalée"
  rule; it is not a silent behavior change since the affected fields are
  the ones this release's audit specifically targeted.
- Rows with `airtightness_n50 == 0` are unaffected in the n50 branch (falls
  back to `infiltration_ach` exactly as before) but do still pick up the
  new door/window opening increment at their stored (default or explicit)
  frequency.

`greencube.cooling.ventilation.profile` also gains the same
validated-study write/unlink lock that `occupancy_profile.py` already had
(previously absent from this model entirely — a validated study's
ventilation data could be edited in place with no revision, an immutability
gap this release closes).

## 18.0.6.0.2 (GC-COOLING-16)

Pure bugfix/read-path fix, no schema impact, no migration script:

- `_serialize_result()` (controller) now looks up the job that produced a
  result and includes `job_id`, `requested_engine`, and
  `energyplus_processing_status` in `GET /results/<id>`, and adds
  `is_current` (`True` only when the result is the study's
  `active_result_id`). No new stored field, no new column — everything
  returned is derived at serialization time from data that already exists
  (`greencube.cooling.calculation.job`, `greencube.cooling.calculation
  .snapshot.requested_engine`, `greencube.cooling.study.active_result_id`).
  This closes the GC-COOLING-16 audit finding that the frontend was
  treating the job-creation response as if it were the full result, and
  had no backend-provided way to detect a stale/superseded result.
- Frontend (`frontend/src/api/study.ts`, `ResultsPage.tsx`,
  `ReviewStep.tsx`) updated to match this contract: job and result are
  fetched and typed as distinct objects, the EnergyPlus hand-off is polled
  by `job_id` with a capped backoff and stops on a terminal status, and a
  result flagged `is_current: false` shows a stale-result banner instead of
  silently presenting it as current. `ResultsPage` never issues
  `POST /calculations` on mount, refresh, or back-navigation — only from an
  explicit button click (Review's "Lancer le calcul" or Results' own
  "Relancer le calcul"), each with its own fresh `Idempotency-Key`.

No existing stored data changes meaning or shape: this release adds no
columns and no fields to any model.

Like the rest of this module (see `docs/cooling_v2_traceability_matrix.md`),
no migration script here has been executed against a real Odoo instance
with pre-existing data. `18.0.2.0.0/post-migrate.py` was reviewed by
reading and by `ast.parse`, not by running an actual `-u` upgrade.

## 18.0.6.0.3 (GC-COOLING-08)

Pure bugfix/frontend-correctness fix, no schema impact, no migration
script: `greencube.thermal.specification.roof_u_value`/`floor_u_value`
already existed as their own required columns (catalog model, versioning,
`source_template_id`/`source_template_version` provenance, and the
`gc-studio`/`gc-office`/`gc-living`/`gc-commerce` catalog data with
genuinely distinct dimensions/U-values were already in place from earlier
sessions) — the only real gap was the frontend, which derived roof/floor
U-values from `wall_u_value * 0.9` / `* 1.1` instead of reading the
catalog's own `roof_u_value`/`floor_u_value` fields, silently discarding
each template's real envelope performance and making "Personnalisé" unable
to set them independently.

- `frontend/src/types/study.ts`: added `roofUValueWm2k`/`floorUValueWm2k`
  to `ModelData`.
- `frontend/src/sync/syncStudy.ts`: sync these two fields directly to/from
  `wall_u_value`/`roof_u_value`/`floor_u_value` instead of computing them
  from a fixed ratio.
- `frontend/src/routes/steps/ModelStep.tsx`: applying a catalog template
  now sets roof/floor U-value from the template; "Personnalisé" exposes
  all three (wall/roof/floor) as independently editable fields; an
  "inherited from catalog" vs. "modifié pour cette étude" badge is shown
  whenever a template is applied, and a "Réappliquer le modèle catalogue"
  action previews the exact field-by-field diff and requires explicit
  confirmation before overwriting a customization (a version bump or a
  reload must never silently discard a customization).
- `addons/greencube_cooling/services/api_validation.py`: added
  `wall_u_value`/`roof_u_value`/`floor_u_value`/`window_u_value` to
  `FIELD_LIMITS` (0.05–6.00 W/m².K) so an out-of-range U-value — previously
  only rejected by the `> 0` SQL CHECK constraint, letting e.g.
  `wall_u_value=999` through — is now caught by the same structured 422
  `VALIDATION_ERROR` path as every other bounded field.
- `addons/greencube_cooling/controllers/api.py`: facade validation now also
  checks `window_u_value` against that same bound.

## 18.0.6.0.4 (GC-COOLING-09)

Additive schema change, ORM auto-backfill is correct, no migration script:

- `greencube.cooling.result` gains one new optional field,
  `solar_gain_by_facade_json` (`Text`, defaults to empty/`None`). Existing
  result rows simply have no per-facade breakdown (correct: they predate
  this feature and were never computed with it) — `GET /results/<id>`
  falls back to `"solar_gain_by_facade": []` for them via
  `json.loads(result.solar_gain_by_facade_json or "[]")`, exactly the same
  pattern already used for `warnings_json`/`main_load_drivers_json`.

Audit findings addressed (orientation/façades/vitrages/protections had
already been substantially fixed in earlier sessions — see the "already
in place" note in each item below):

- Orientation rotation (`rotatedOrientation`/`facadeSlotForOrientation`,
  `frontend/src/sync/syncStudy.ts`) and per-type shading efficiency
  (`PROTECTION_TYPE_CONFIG`) were already implemented and already covered
  by `frontend/src/sync/syncStudy.test.ts` before this session — verified
  by inspection, not re-implemented, to avoid duplicating working code.
- The one genuine remaining gap found: MERCURE's `breakdown` only ever
  exposed a single aggregate `solar_glazing` total across all glazed
  facades, with no way to tell which orientation actually drives the
  solar load (GC-COOLING-09 pt.11 — "rendre visibles dans les résultats
  les principaux gains solaires par façade" — was not yet done). Fixed by
  adding `FacadeSolarGain` (`services/mercure/schemas.py`) and populating
  `MercureScenarioResult.solar_gain_by_facade` in `engine.py`'s
  `_solar_glazing_gain()`, persisted via the new field above and exposed
  as `solar_gain_by_facade` on `GET /results/<id>`. It is a pure
  decomposition of the existing `solar_glazing` breakdown entry (asserted
  by `test_mercure_engine.py::SolarGainByFacadeTestCase` and
  `test_http_api.py::test_result_exposes_solar_gain_by_facade`) — never an
  additional load on top of `total_load_w`.
- Also newly covered: HTTP tests for `GET/PUT /studies/<id>/shading`
  (distinct entries per orientation/type, and that a UI removal — a PUT
  with fewer/zero entries — actually deletes the dropped backend records,
  GC-COOLING-09 pt.8), which had no HTTP-level test before this session
  despite the endpoint itself already existing.
- `docs/api_routes.md` documents the azimuth convention, the fact that the
  richer `greencube.cooling.shading` records (schedule, `automatic`,
  provenance) do not yet feed the MERCURE physics directly — only each
  facade's own `default_shading_factor` does — as an explicit, documented
  MVP simplification (GC-COOLING-09 pt.12), not a silent gap.
- `addons/greencube_cooling/tests/test_http_api.py`: added HTTP-level
  coverage for the catalog listing (distinct values per model), a
  template's resolved values freezing into the study's own specification,
  a customization surviving a re-fetch (never silently reset), a catalog
  template version bump not retroactively mutating an already-forked
  study, and rejection of an out-of-range U-value / negative facade
  surface / inconsistent glazing area.

No existing stored data changes meaning or shape: this release adds no
columns and no fields to any model — every field involved
(`wall_u_value`, `roof_u_value`, `floor_u_value`, `source_template_id`,
`source_template_version`) already existed.

## 18.0.7.0.0 (GC-COOLING-10)

Schema change requiring a migration script — bumps the third digit:

- `greencube.cooling.occupancy.profile` gains seven new boolean columns,
  `active_monday` .. `active_sunday`, which become the authoritative weekly
  calendar. The previous `usage_days` `Char` ("Mon-Fri") is kept, unchanged,
  as a legacy/display-only field — it is no longer written by new code and
  no longer read by `cooling_study.py`'s MERCURE input builder — but a
  free-text field can neither be validated nor safely consumed by the
  solver or by a future Honeybee/EnergyPlus schedule mapping, hence the
  new structured fields (README_GC-COOLING-10 §"Format des horaires":
  "Ne pas stocker le planning en texte libre").
  `migrations/18.0.7.0.0/post-migrate.py` backfills the new booleans from
  each existing row's own `usage_days` text on a best-effort basis (a
  handful of recognized patterns: "Mon-Fri"/"Lun-Ven", "7/7"/"every day",
  "weekend"/"sat-sun"; anything else falls back to the same Monday-Friday
  default a brand-new profile gets) — needed because the ORM's own
  per-column default would otherwise silently give every existing row
  Monday-Friday regardless of what its `usage_days` text actually said.
- Three new stored computed fields — `daily_occupied_hours`,
  `crosses_midnight`, `occupancy_fraction` — derived purely from
  `start_hour`/`end_hour`, which are unaffected by this migration: Odoo's
  own compute-on-upgrade backfill is correct for these, no script needed.
  `occupancy_fraction` (average fraction of the day occupied, matching
  equipment/lighting's existing daily-average simplification) now feeds
  `Occupancy.occupancy_fraction` in the MERCURE input in place of a
  previously hardcoded `1.0` — the actual bug this session fixes: the
  Usage screen's schedule/hours previously had **zero** effect on the
  calculated occupant sensible/latent gains.
- `usual_occupants`/`maximum_occupants` bounds tightened from `(0, 10000)`
  to `(0, 500)`/`(0, 1000)` in both `api_validation.FIELD_LIMITS` and the
  model's own `_check_occupants` constrain (README's explicit "habituel :
  0 à 500 ; maximum : 0 à 1000"). No existing test or fixture data exceeds
  these bounds (checked by grep before tightening).
- `greencube.cooling.occupancy.profile.write()`/`.unlink()` now raise
  `UserError` once the parent study is `validated`, mirroring
  `greencube.cooling.study.write()`'s own `LOCKED_STATES` guard — which
  never actually covered this sub-model. `POST/PUT .../occupancy-profile`
  maps this to `409 INVALID_STATE` instead of leaking a raw `UserError`
  through the "study locked" 500. `action_create_revision()`'s `copy()`
  calls are unaffected (`copy()` creates a new record on the new draft
  revision, it never calls `write()`/`unlink()` on the validated original).

## 18.0.8.0.0 (GC-COOLING-11)

Additive schema change, ORM auto-backfill is correct for all existing
rows, no migration script needed:

- Inspected the current repo state first: `greencube.cooling.equipment.load`
  (quantity/power/simultaneity/dissipation/provenance/thermal_load_w),
  the full CRUD HTTP surface (`GET/POST .../equipment-loads`,
  `PATCH/DELETE /equipment-loads/<id>`), and the frontend sync loop
  (`syncStudy.ts`'s `syncEquipment()`, diffing by `backendId` instead of
  delete/recreate) already existed from earlier sessions — not
  duplicated. The genuine gap (README_GC-COOLING-11 "ne jamais coder les
  équipements directement dans le frontend" / "le catalogue vient
  d'Odoo"): the Equipment step's list of *offered* internal-load
  templates (laptop, monitor, printer, server, LED lighting, coffee
  machine, network gear, battery, UPS) was a static TypeScript array
  (`frontend/src/equipment/internalLoadsCatalog.ts`) with no backend
  source at all, unlike the cooling-equipment-to-install catalog
  (`is_cooling_equipment` on `product.template` / `GET
  /equipment-catalog`), which already followed the catalog-in-Odoo
  pattern.
- `product.template` gains five new optional fields:
  `is_internal_load_equipment` (Boolean, default `False`),
  `internal_load_code` (Char), `internal_load_category` (Selection,
  mirrors `greencube.cooling.equipment.load.category`),
  `internal_load_unit_power_w` / `internal_load_usage_hours_per_day` /
  `internal_load_simultaneity_percent` (Float). `False`/`""`/`0.0` are
  correct for every pre-existing product (none of them were ever an
  internal-load catalog entry) — plain additive columns, no backfill
  needed.
- `data/cooling_internal_load_catalog_data.xml` (new, `noupdate="1"`)
  seeds the same 9 reference items the frontend used to hardcode, with
  the same reference values, so this change does not silently alter what
  a new study is offered.
- `controllers/api.py`: new `GET /equipment-load-catalog` (mirrors the
  existing `GET /equipment-catalog` pattern) serializes
  `is_internal_load_equipment=True` products.
- `_serialize_equipment_load`/`_equipment_load_vals` unchanged
  (`product_id` was already a field on the line and already
  round-tripped); `syncStudy.ts` now also sends `product_id` when a line
  originates from the catalog, and matches a reloaded backend line back
  to its catalog card by `product_id` first, falling back to the
  previous name-based heuristic only for legacy custom lines that predate
  this change.
- `frontend/src/types/study.ts`: `EquipmentItem.category` widened from
  `'it' | 'lighting' | 'appliance' | 'network' | 'other'` to the full set
  already accepted by the backend model's `category` Selection
  (`kitchen`, `battery`, `inverter`, `medical`, `machine` added) — the
  catalog's `battery`/`ups` entries now carry their real
  `battery`/`inverter` category instead of being silently folded into
  `other`.

No existing stored data changes meaning or shape: every new field is
optional/additive, and no previously-stored
`greencube.cooling.equipment.load` row is touched by this release.

## 18.0.10.0.0 (GC-COOLING-04)

Adds provenance/governance fields to `greencube.cooling.climate.dataset`:
`dataset_type` (Selection, default `"historical_observed"` — correct for
every pre-existing row, since the service has only ever produced
historical-observed data), `provider_code`, `provider_version`,
`schema_version`, `license`, `timezone`, `variables`, `checksum`,
`fetched_at`, `active` (Boolean, default `True`), `superseded_by_id`
(Many2one, self). All new optional fields with a default that is equally
valid for old and new rows — no script needed, ORM auto-backfill is
correct. Pre-existing cached dataset rows simply have an empty
`checksum`/`provider_code`/etc. until their cache key next expires and
they are refreshed (never retroactively rewritten in place — see
`docs/climate_service.md` §4).

Adds `dataset_id` (Many2one to `greencube.cooling.climate.dataset`),
`dataset_type` and `checksum` to `greencube.cooling.climate.scenario` —
same additive/optional pattern, no script needed. Pre-existing scenario
rows (written by a prior calculation) simply have these three fields
empty until the next `action_calculate()` on their study repopulates them.

Behavioural change (not a schema/data migration, but worth flagging
here): `climate.dataset.get_or_fetch_scenarios()` no longer calls
`write()` on an existing dataset row when its cache TTL has expired — it
now archives the old row (`active=False`, `superseded_by_id=<new id>`)
and creates a brand-new row instead (see `docs/climate_service.md` §4).
This means the `greencube.cooling.climate.dataset` table will accumulate
soft-archived rows over time instead of being update-in-place; no cleanup
job is introduced in this pass (see the README's "Rétention et nettoyage"
section — a `cooling_cleanup_expired_climate_artifacts` cron is explicitly
out of scope here, left for a dedicated retention-policy pass since it
touches snapshot/result immutability guarantees this release did not
otherwise need to change).

Also fixes a frontend-only false claim (no schema impact): the Location
step's "Données récupérées automatiquement" list used to show "📈
Projections climatiques" next to a list of historical-data facts, wrongly
implying a forward-looking climate-projection model was in use. Corrected
to "Historique multi-année (10 ans)" — see `docs/climate_service.md` §2.

## 18.0.11.0.0 (GC-COOLING-14)

Adds `fan_fraction_dissipated_in_zone` (Float, default `1.0`) to
`greencube.cooling.ventilation.profile` — new optional field with a default
that is valid for both old and new rows (1.0 reproduces exactly the value
`_build_mercure_input()` used to hardcode for every study before this
change), so no migration script is needed; ORM auto-backfill is correct.

Two pure-logic fixes in `_build_mercure_input()`, no schema/data migration
needed:

- `ventilation.fan_fraction_dissipated_in_zone` sent to MERCURE is now read
  from the ventilation profile above instead of being hardcoded to `1.0`
  regardless of it (silently ignoring e.g. a `dedicated_mechanical`/
  `double_flow` AHU whose fan sits outside the conditioned zone).
- `infiltration.method` sent to MERCURE is now `"ach"` when the effective
  infiltration rate came from a plain manually-entered `infiltration_ach`
  (no `airtightness_n50` measured/estimated), and only `"n50_estimated"`
  when an actual n50 value was used — it used to be hardcoded to
  `"n50_estimated"` in every case, which wrongly fired the
  `LOW_CONFIDENCE_INFILTRATION` warning and applied MERCURE's confidence-
  score penalty even for studies whose infiltration figure was not an n50
  estimate at all.

Both fixes only change *future* calculations (new snapshots/results);
already-frozen `greencube.cooling.calculation.snapshot` and
`greencube.cooling.result` rows are immutable and unaffected, per the
module's snapshot/result immutability guarantee.

Also adds a shared numeric golden-reference fixture
(`addons/greencube_cooling/tests/fixtures/mercure_golden_reference.json`,
mirrored as `frontend/src/mercure/golden_reference.ts`) so the Python
(canonical) and TypeScript (non-production reference port) MERCURE engines
are checked against the same expected numbers with an explicit relative
tolerance — no schema impact, test-only.

## 18.0.12.0.0 (GC-COOLING-18)

Adds three new fields to `greencube.cooling.equipment.selection`:
`validated_at` (Datetime), `validator_id` (Many2one res.users) and
`supersedes_id` (Many2one self, `ondelete="set null"`). All three are new,
optional and `False`/`None` on every pre-existing row — ORM auto-backfill
is correct, no data migration script needed.

Three behavioural fixes, no schema/data migration needed beyond the fields
above:

- `greencube.cooling.equipment.selection` gains `action_validate()`, the
  only path that promotes a "selected" working choice to the immutable
  "validated" state; exposed as `POST .../equipment-selections/<id>/validate`
  and a "Valider" action in the frontend history list. Before this change
  nothing ever moved a selection to "validated", so the model's own
  write()/unlink() immutability guard never actually engaged.
- `greencube.cooling.study.unlink()` now refuses to delete a study that has
  a validated equipment selection. `equipment_selection_ids` carries
  `ondelete="cascade"`, which Postgres enforces as a raw SQL `ON DELETE
  CASCADE` constraint — it silently bypassed
  `equipment.selection.unlink()`'s own guard entirely, since the child rows
  were removed directly by the database rather than through the child
  model's Python `unlink()`. The guard now also lives at the one layer
  that is actually invoked.
- `security/greencube_cooling_rules.xml`: `rule_equipment_selection_company`
  was the *only* ir.rule for the model and was scoped to
  `group_greencube_cooling_user` instead of being global — combined with
  the complete absence of a per-user ownership rule, any User-group member
  could read/write another user's equipment selection as long as it
  belonged to the same company (IDOR). Fixed to mirror the
  company-global/own-user/technician-company pattern already used by
  equipment_load/ventilation_profile/occupancy_profile/calculation_snapshot.
  On upgrade (not just fresh install), clearing the rule's previously
  non-empty `groups` many2many requires an explicit `(6, 0, [])` command —
  a bare `eval="[]"` has no commands and therefore leaves an
  already-installed database's stored value untouched.

Also fixes `services/compatibility.py`'s recommendation ranking: a missing
or zero product capacity/outdoor-temperature/SHR now yields an explicit
`insufficient_data` status instead of silently computing as
`oversizing_ratio = 0.0`, and the recommendation list is sorted by a
stable `(status_rank, |oversizing_ratio − 1|, product_id)` key
(`recommendation_sort_key()`) instead of a raw ascending sort on
`oversizing_ratio` alone — the latter used to float products with missing
technical data to the very top of the recommended list, ahead of
genuinely well-matched equipment.

## 18.0.14.0.0 (GC-COOLING-15)

Adds two new fields to `greencube.cooling.calculation.job`: `attempt_count`
(Integer, default `0`) and `max_attempt_count` (Integer, default `3`). Both
are new, required-with-default, and backfilled to their default by the ORM
on every pre-existing row — no data migration script needed. Extends the
`energyplus_processing_status` selection with one new value, `cancelled`;
extending a Selection field's allowed values is backward compatible (no
existing row uses a value being removed).

Adds one new `ir.cron` record (`data/energyplus_job_cron.xml`,
`ir_cron_requeue_stalled_energyplus_jobs`) that runs every 5 minutes. It
only calls `_requeue_stalled_energyplus_jobs()`, which reads/writes
`greencube.cooling.calculation.job` bookkeeping fields
(`energyplus_processing_status`/`claimed_at`/`attempt_count`/
`error_message`) — it never calls `run_energyplus_simulation()` and never
runs inside the same process as an actual EnergyPlus invocation, so it
does not reintroduce the in-process-execution problem GC-COOLING-15's
worker split was written to fix.

Behavioural additions, no breaking changes to any existing endpoint or
field:
- `models/calculation_job.py`: `_claim_next_for_worker()` now uses
  `SELECT ... FOR UPDATE SKIP LOCKED` (raw SQL) instead of a plain ORM
  `search()+write()`, so two concurrent worker processes calling
  `POST /energyplus-jobs/claim` cannot be handed the same job — this is
  the actual "un seul worker doit exécuter un job donné" guarantee, not a
  best-effort one. `action_cancel_energyplus()` is new (only permitted
  while `energyplus_processing_status == 'queued_for_worker'`).
  `_requeue_stalled_energyplus_jobs()` is new (stall detection + bounded
  retry + dead-letter, driven by the new cron above and the new
  `greencube_cooling.energyplus_stall_timeout_seconds` config parameter,
  default 900s).
- `controllers/api.py`: new route
  `POST /api/v1/greencube/cooling/calculations/<job_id>/cancel`
  (`auth="user"`, same ir.rule ownership/company scoping as the existing
  `GET /calculations/<job_id>`).

No behavioural change to MERCURE's synchronous `action_calculate()` path,
to the existing `/energyplus-jobs/claim`/`/energyplus-jobs/<id>/complete`
request/response shapes, or to any already-frozen
`greencube.cooling.result`/`greencube.cooling.calculation.snapshot`/
`greencube.cooling.simulation.artifact` row.

## 18.0.13.0.0 (GC-COOLING-05A)

Adds three new fields to `greencube.cooling.calculation.job`:
`solver_version_id` (Many2one `greencube.cooling.solver.version`,
`ondelete="restrict"`), `weather_artifact_id` (Many2one
`greencube.cooling.simulation.artifact`, `ondelete="restrict"`) and
`simulation_options_json` (Text, default `"{}"`). All three are new,
optional, and unpopulated (`False`/`"{}"`) on every pre-existing row — ORM
auto-backfill is correct, no data migration script needed. Nothing today
writes `solver_version_id`/`weather_artifact_id` yet; they complete the
GC-COOLING-05A pt.10 "serializable job contract for the future worker"
(snapshot_id/requested_engine already existed) ahead of the actual
EnergyPlus worker orchestration.

No behavioural change to MERCURE's synchronous `action_calculate()` path
or to any already-frozen `greencube.cooling.result`/
`greencube.cooling.calculation.snapshot` row.

`services/energyplus.py` gains `get_component_versions()` and
`check_compatibility()` (pinned honeybee-energy/ladybug/EnergyPlus/
OpenStudio version matrix — see `docs/honeybee_energyplus_mvp.md`), and
`check_availability()`'s `detail` string now includes detected versions
and an "UNPINNED VERSION WARNING" if present-but-off-matrix — its
`(bool, str)` return signature and the `available=False` -> "Missing: ..."
message shape used by existing callers are unchanged, so this is
additive, not breaking.

Also adds test coverage: `services/energyplus.py` previously had no
dedicated unit tests at all (feature flag on/off, availability detection,
the two distinct error types) — now covered by
`tests/test_energyplus_service.py`. `tests/test_honeybee_translator.py`
gains orientation/area-convention, invalid-U-value and
unmatched-glazing-facade coverage that the condensed GC-COOLING-05A test
list required and that was previously missing.
