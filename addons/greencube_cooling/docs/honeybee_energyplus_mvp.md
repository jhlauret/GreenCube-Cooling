# Honeybee / EnergyPlus MVP socle (GC-COOLING-05A)

## Scope of this lot

This lot delivers the **first, deliberately limited** bridge between a
GreenCube study's frozen calculation snapshot and a Honeybee-shaped model,
plus a job/artifact contract ready for a future EnergyPlus worker. It does
**not** run EnergyPlus, does not produce a physical simulation result, and
must never be described as doing so.

```
greencube.cooling.study (Odoo, source of truth)
        │  action_calculate(engine="energyplus"|"both")
        ▼
services/mercure/honeybee_translator.py  (pure Python, no Odoo import)
        │  build_honeybee_model(mercure_input) -> (model_dict, diagnostics)
        ▼
ir.attachment (private, binary) + greencube.cooling.simulation.artifact
        │  (checksum, type=honeybee_json — reference only, never inline text)
        ▼
greencube.cooling.calculation.job.energyplus_processing_status = "queued_for_worker"
        │
        ▼ (future: energyplus_worker/, HTTP claim/complete, GC-COOLING-15)
services/energyplus.py::run_energyplus_simulation()
        │  gated by GC_COOLING_ENERGYPLUS_ENABLED (default false)
        ▼
EnergyPlusUnavailableError | EnergyPlusSimulationError
   (never a fabricated result — see "Honest failure" below)
```

## What actually works today

- `build_honeybee_model(mercure_input)` (`services/mercure/honeybee_translator.py`)
  translates a frozen `MercureInput` snapshot into a deterministic,
  SHA-256-checksummed, Honeybee `Model`/`Room`/`Face`/`Aperture`-shaped
  JSON dict: 4 cardinal wall faces + roof + floor, apertures attached to
  their facade, occupancy/lighting/equipment/infiltration/ventilation/
  setpoints folded into per-zone properties.
- It **rejects** (raises `HoneybeeTranslationError`, never silently
  substitutes a default):
  - non-positive geometry dimensions;
  - non-positive wall/roof/floor U-values;
  - a glazing facade whose area exceeds its wall's gross area.
- It **warns but continues** when a glazing facade has no matching wall
  (logged in `diagnostics.warnings`, aperture skipped).
- Every MVP simplification is recorded in `diagnostics.assumptions`
  (see "Physical limitations" below) — nothing is silently hidden.
- `services/energyplus.py::check_availability()` / `get_component_versions()`
  / `check_compatibility()` detect the actually-installed honeybee-energy,
  ladybug, EnergyPlus binary and (if present) OpenStudio versions and
  compare them against this lot's pinned/tested compatibility matrix
  (`COMPATIBLE_*_VERSION` constants). Detection never fabricates a
  version: an absent component is reported as `None`, not "assumed fine".
- `is_energyplus_enabled()` gates every EnergyPlus-adjacent code path
  behind `GC_COOLING_ENERGYPLUS_ENABLED` (default `false`).
- `greencube.cooling.calculation.job` carries a serializable job contract
  (`snapshot_id`, `requested_engine`, `solver_version_id`,
  `weather_artifact_id`, `simulation_options_json`) ready for a future
  worker to consume, plus `energyplus_processing_status` tracking the
  hand-off independently of the job's own MERCURE-driven `status`.
- Artifacts are stored as `ir.attachment` (private) referenced by a typed,
  checksummed, immutable `greencube.cooling.simulation.artifact` row —
  never as a big text/binary field directly on the job.

## What is deliberately NOT built in this lot

- **No real Honeybee objects are constructed.** The exported JSON is
  shaped like Honeybee's `Model.to_dict()` output closely enough to be a
  real starting point, but it is produced with plain dicts, not the
  `honeybee-energy`/`honeybee-core` classes (not installed in this
  environment — a ~600MB EnergyPlus binary plus several heavy Python
  packages, not a stack you casually `pip install` into a web server).
- **No EnergyPlus execution.** `run_energyplus_simulation()` in
  `services/energyplus.py` always raises: `EnergyPlusUnavailableError` if
  the stack is missing (true in every environment this code has run in so
  far), or `EnergyPlusSimulationError("... not implemented yet ...")` if
  the stack were somehow present — the actual translation-to-IDF and
  simulation run belongs to GC-COOLING-15's fuller worker scope, not this
  lot.
- **No weather (EPW) resolution.** `weather_artifact_id` exists as a job
  field for the future contract but nothing populates it yet — this MVP's
  translated model carries no weather reference at all. `artifact_type =
  "epw"` already exists on `simulation.artifact` as a forward-declared
  slot, but no code path produces one.
- **No multi-zone geometry.** One GreenCube = one Honeybee `Room`, per the
  README's explicit MVP scope; the face/aperture list shape is written to
  be extensible to multiple rooms later without a rewrite, but nothing
  today constructs more than one.
- **No layered material constructions.** Each construction (wall/roof/
  floor/glazing) is exported as a single equivalent-U-value pseudo-layer.
  A real Honeybee `OpaqueConstruction` needs individual material
  thickness/conductivity/density/specific-heat, which the MERCURE snapshot
  does not carry — building that out is out of scope here (README's
  "Parois opaques" section, not the condensed GC-COOLING-05A worklist).
- **No dynamic/geometric shading.** Solar protections are folded into one
  static `static_shading_transmittance` multiplier per aperture, not a
  scheduled or geometric Honeybee `Shade`.

## Physical limitations of the MVP model (do not present as a full result)

1. **Single zone.** No inter-room heat transfer, no zone-to-zone airflow.
2. **Ideal, not real, HVAC.** No commercial-equipment behaviour is
   modeled at this stage — there is no HVAC object in the exported model
   at all yet (deferred to GC-COOLING-15's actual translation).
3. **Static shading factor.** Time-varying blind/shutter use is not
   captured; a single number multiplies every hour equally.
4. **Equivalent-U-value constructions.** No thermal mass/inertia is
   modeled — a lightweight and a heavyweight wall of the same U-value
   translate identically.
5. **Aggregated internal loads.** All equipment is summed into one power
   density for the room; individual equipment schedules are lost.
6. **No weather.** The translated model has no EPW/design-day attached;
   it cannot be simulated as-is even once EnergyPlus itself is available.
7. **No thermal bridges beyond MERCURE's existing correction.** Whatever
   thermal-bridge adjustment the MERCURE snapshot already applied to its
   U-values passes through as-is; nothing new is added at the Honeybee
   translation layer, avoiding double-counting.

## Feature flag

`GC_COOLING_ENERGYPLUS_ENABLED` (default unset/`false`) gates:

- the Honeybee JSON translation attempted inline by
  `cooling_study._process_energyplus_translation()` (when disabled, a
  study requesting `engine=energyplus`/`both` gets an
  `ENERGYPLUS_DISABLED` warning and `result_state="partial"`, never a
  silent MERCURE-only result presented as if EnergyPlus had run);
- every EnergyPlus-adjacent code path in `services/energyplus.py`.

## Compatibility matrix (pinned, tested-against versions)

| Component        | Pinned version | Required for MVP availability? |
|-------------------|-----------------|-------------------------------|
| honeybee-energy   | 1.106.5         | yes |
| ladybug           | 0.42.5          | yes |
| EnergyPlus binary | 23.2.0          | yes |
| OpenStudio        | 3.6.1           | no (informational only — this MVP's translation path targets Honeybee → EnergyPlus directly, not via OpenStudio) |

`check_availability()` still reports `available=True` if the stack is
present but on an unpinned version (with an explicit warning in its
`detail` string and a logged warning) — presence gates availability, the
version match only gates the *compatibility* verdict, so a real-but-
untested newer version is never silently reported as "not installed".

## Never claim EnergyPlus is operational without proof

Every test in `tests/test_energyplus_service.py` that exercises
`check_availability()`/`run_energyplus_simulation()` against the real
(uninstalled, in this repo's tested environments) stack asserts the
*unavailable* path — that is the honest, verified state of this
environment. The one test that would exercise a real Honeybee model
validation (`RealHoneybeeValidationTestCase`) is explicitly
`@unittest.skipUnless(honeybee_energy installed)`, not mocked to appear
green.
