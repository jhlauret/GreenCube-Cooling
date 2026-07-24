# -*- coding: utf-8 -*-
"""Server-side range validation for the JSON API (GC-COOLING-02 §10).

The frontend's Zod schemas validate the same fields, but per the mandate
("La validation Zod du frontend ne remplace jamais la validation Odoo"),
every bound in README_GC-COOLING-02_API_ODOO.md §10.1 must also be
enforced here, independent of and in addition to whatever the client did
or failed to do.

FIELD_LIMITS maps a field name to an inclusive (min, max) bound. It is
intentionally a flat namespace (not modeled per-route) since none of these
field names currently collide in meaning across the routes that use them.
"""
import math

FIELD_LIMITS = {
    "latitude": (-90, 90),
    "longitude": (-180, 180),
    "altitude_m": (-500, 9000),
    "cooling_setpoint_c": (16, 35),
    "maximum_acceptable_temperature_c": (16, 35),
    "target_humidity_percent": (20, 90),
    "length_m": (0, 100),
    "width_m": (0, 100),
    "height_m": (0, 20),
    # GC-COOLING-08 §"Enveloppe thermique": 0.05-6.00 W/m².K covers
    # everything from a super-insulated passive envelope to an
    # uninsulated single-glazed opening; anything outside is either a
    # unit-confusion bug (e.g. mm instead of m, or a resistance value
    # entered where a U-value was expected) or a physically absurd input,
    # and was previously only rejected by the ">0" SQL CHECK constraint,
    # letting e.g. wall_u_value=999 through silently.
    "wall_u_value": (0.05, 6.0),
    "roof_u_value": (0.05, 6.0),
    "floor_u_value": (0.05, 6.0),
    "window_u_value": (0.05, 6.0),
    # GC-COOLING-10: bounds per README_GC-COOLING-10_USAGE_OCCUPATION.md
    # §"Nombre d'occupants" ("habituel : 0 à 500 ; maximum : 0 à 1000").
    # Previously (0, 10000) for both, which let clearly absurd occupant
    # counts through this layer (the model-level constrains now mirror
    # the same 500/1000 caps as defense in depth).
    "usual_occupants": (0, 500),
    "maximum_occupants": (0, 1000),
    "start_hour": (0, 24),
    "end_hour": (0, 24),
    "airflow_m3h": (0, 1000000),
    "unit_power_w": (0, 10000000),
    "fan_power_w": (0, 10000000),
    "sensible_gain_per_person_w": (0, 10000000),
    "simultaneity_percent": (0, 100),
    "efficiency_percent": (0, 100),
    "heat_recovery_efficiency_percent": (0, 100),
    "usage_hours_per_day": (0, 24),
    "solar_factor_g": (0, 1),
    "visible_transmittance": (0, 1),
    # GC-COOLING-12: airtightness/infiltration bounds per
    # README_GC-COOLING-12_VENTILATION_CONFORT.md ("n50" 0-30 vol/h at 50 Pa;
    # ACH kept generous since some dedicated/process ventilation legitimately
    # runs well above typical residential values).
    "airtightness_n50": (0, 30),
    "infiltration_ach": (0, 50),
    "air_changes_per_hour": (0, 50),
    # GC-COOLING-14: share of fan electrical power dissipated as sensible
    # heat inside the conditioned zone; always a fraction, never negative
    # or above unity.
    "fan_fraction_dissipated_in_zone": (0, 1),
}


def validate_ranges(vals, limits=FIELD_LIMITS):
    """Returns {field: [message, ...]} for every field present in `vals`
    that is out of bounds, non-numeric where a number is required, or
    non-finite (NaN/Infinity). Fields absent from `vals` or from `limits`
    are not checked here (unknown-field rejection is a separate concern —
    every route already only extracts a fixed allow-list of keys before
    calling this, so unknown fields are structurally dropped, not merely
    unchecked)."""
    errors = {}
    for field_name, value in vals.items():
        if field_name not in limits or value is None:
            continue
        lo, hi = limits[field_name]
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            errors.setdefault(field_name, []).append("Must be a number.")
            continue
        if math.isnan(numeric) or math.isinf(numeric):
            errors.setdefault(field_name, []).append("Must be a finite number.")
            continue
        if numeric < lo or numeric > hi:
            errors.setdefault(field_name, []).append(f"Must be between {lo} and {hi}.")
    return errors
