# -*- coding: utf-8 -*-
"""Centralized physical constants for MERCURE.

Per README_GC-COOLING-14_MERCURE.md: every constant must be named,
valued, unit-tagged, sourced and versioned. This module has no
dependency on the Odoo ORM so it can be tested in isolation.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalConstant:
    name: str
    value: float
    unit: str
    source: str
    version: str


AIR_DENSITY = PhysicalConstant(
    name="air_density",
    value=1.2,
    unit="kg/m3",
    source="ASHRAE Fundamentals, 20 C sea level approximation",
    version="1.0",
)

AIR_SPECIFIC_HEAT = PhysicalConstant(
    name="air_specific_heat",
    value=1006.0,
    unit="J/kg.K",
    source="ASHRAE Fundamentals",
    version="1.0",
)

LATENT_HEAT_OF_VAPORIZATION = PhysicalConstant(
    name="latent_heat_of_vaporization",
    value=2_501_000.0,
    unit="J/kg",
    source="ASHRAE Fundamentals, 0 C reference",
    version="1.0",
)

WATTS_PER_BTU_H = 0.29307107

MERCURE_ENGINE_CODE = "MERCURE"
MERCURE_ENGINE_VERSION = "1.0.0"
MERCURE_METHOD_VERSION = "1.0"

# Additional natural-infiltration ACH contributed by voluntary door/window
# opening, on top of the n50-derived or manually entered baseline
# infiltration_ach. Each level is an explicit, versioned estimate (not a
# measurement) — deliberately conservative and additive per opening type
# (a door and a window being both "frequently" opened are two distinct air
# paths, not a double count of the same one) so it can be revised without
# touching call sites (GC-COOLING-12).
OPENING_FREQUENCY_ACH_INCREMENT = {
    "rare": 0.0,
    "occasional": 0.03,
    "frequent": 0.08,
    "continuous": 0.15,
}
OPENING_INCREMENT_METHOD_VERSION = "1.0"
