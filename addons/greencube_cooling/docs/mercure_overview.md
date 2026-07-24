# MERCURE — canonical engine overview (GC-COOLING-14)

## Canonical implementation

`addons/greencube_cooling/services/mercure/` (Python) is the **only**
production/contractual implementation of the MERCURE engine. It has no
Odoo ORM dependency (pure dataclasses and functions) and is invoked from
`greencube.cooling.study.action_calculate()`.

`frontend/src/mercure/engine.ts` is a TypeScript port kept **only** as a
non-regression reference: it is not imported by any route under
`frontend/src/routes`, and it must never become a second source of truth.
Its sole purpose is `engine.test.ts`, which is checked against the same
numeric golden reference as the Python test suite (see below) so the two
cannot silently drift apart if either is edited without the other.

## Versioning

- `engine_code = "MERCURE"`, `engine_version = "1.0.0"`,
  `calculation_method_version = "1.0"` — `services/mercure/constants.py`.
- Persisted results reference `greencube.cooling.solver.version` (the
  Odoo-side registry of which engine/version produced a given
  `greencube.cooling.result`); a new engine version never rewrites past
  results (`cooling_calculation_snapshot.py` / `cooling_result.py` both
  reject writes to frozen/superseded rows).

## Determinism and checksum

- `run_mercure()` is a pure function over an immutable `MercureInput`
  dataclass tree: no ORM access, no `datetime.now()`/`time.time()` reads,
  no mutation of its input. Covered by
  `tests/test_mercure_engine.py::DeterminismTestCase`.
- The snapshot's `snapshot_hash` (`cooling_study.py::action_create_snapshot`)
  is a SHA-256 of the serialized `MercureInput` payload — same inputs,
  same hash, same result; `action_calculate()` replays the frozen snapshot
  JSON rather than re-reading the (possibly since-edited) live study.

## Golden reference / TS-Python conformance

`tests/fixtures/mercure_golden_reference.json` (Python) and
`frontend/src/mercure/golden_reference.ts` (TypeScript) hold the same
numbers, generated from the Python engine on the two shared fixtures
(`fixtures.py` / `fixtures.ts`: `studio_standard_input`,
`west_glazed_office_input`). Both test suites assert their own engine's
output against these numbers within a `1e-6` relative tolerance. Diffing
this file without a *documented, deliberate* formula change in both
implementations is a regression, not a routine update.

## Known, deliberately out-of-scope simplifications (see README_GC-COOLING-14)

MERCURE is a fast pre-dimensioning engine, not an hourly dynamic
simulation. This pass keeps the following deliberately unbuilt/simplified,
consistent with the "conservative patch, not a rewrite" mandate for this
campaign:

- No `psychrometrics.py`/`validation.py`/`transmission.py`/... file split —
  the engine stays a single `engine.py` module; the physics it implements
  matches the spec's formulas (verified by the equation-level tests
  already in `test_mercure_engine.py`), but the file layout is not split
  purely for its own sake.
- `enable_opaque_solar_gain` (opaque-surface solar gain) is not
  implemented — glazing solar gain only, as the spec explicitly allows for
  a minimal MVP ("Elle peut rester désactivée dans le MVP minimal").
- Window/door "opening" airflow components (`window_opening_*`,
  `door_opening_*` breakdown codes) are not separately modeled; their
  effect is folded into the ventilation profile's documented door/window
  opening-frequency ACH increment (`OPENING_FREQUENCY_ACH_INCREMENT`,
  GC-COOLING-12), not a full AirflowNetwork/CFD model, per spec.
- `what_if` mode, `compare_mercure_energyplus()`, and a dedicated
  `recommendations.py`/`explainability.py` module are not implemented in
  this pass — recommendations/explainability are out of MVP scope per the
  README's own "Limites du lot" section (EnergyPlus orchestration and
  comparison are GC-COOLING-05A/15/16/17).

## Two real gaps fixed in this pass

1. `ventilation.fan_fraction_dissipated_in_zone` sent to the solver was
   hardcoded to `1.0` in `_build_mercure_input()` regardless of the
   ventilation profile. Now read from a new
   `greencube.cooling.ventilation.profile.fan_fraction_dissipated_in_zone`
   field (default `1.0`, preserving prior behavior for existing studies).
2. `infiltration.method` sent to the solver was hardcoded to
   `"n50_estimated"` in every case, which wrongly fired
   `LOW_CONFIDENCE_INFILTRATION` and penalized the confidence score even
   for a manually-entered, non-n50 `infiltration_ach`. Now derived from
   which value actually fed `get_effective_infiltration_ach()`.

See `migrations/README.md` §18.0.11.0.0 for the full migration note.
