# -*- coding: utf-8 -*-
"""Unit conversions for MERCURE. No Odoo ORM dependency."""
import math

from .constants import WATTS_PER_BTU_H


def watts_to_kw(watts: float) -> float:
    return watts / 1000.0


def watts_to_btu_per_hour(watts: float) -> float:
    return watts / WATTS_PER_BTU_H


def m3h_to_m3s(m3h: float) -> float:
    return m3h / 3600.0


def ach_to_m3h(ach: float, volume_m3: float) -> float:
    if ach < 0:
        raise ValueError("INVALID_UNIT: ach must be >= 0")
    if volume_m3 < 0:
        raise ValueError("INVALID_UNIT: volume must be >= 0")
    return ach * volume_m3


def humidity_ratio_from_temperature_rh(
    temperature_c: float,
    relative_humidity_percent: float,
    pressure_pa: float = 101_325.0,
) -> float:
    """Tetens approximation of saturation vapor pressure, then humidity ratio.

    Sufficient for MVP pre-dimensioning; not a full psychrometrics library.
    """
    svp = 610.94 * math.exp((17.625 * temperature_c) / (temperature_c + 243.04))
    vapor_pressure = (relative_humidity_percent / 100.0) * svp
    return (0.622 * vapor_pressure) / (pressure_pa - vapor_pressure)


def positive_cooling_delta_t(outdoor_c: float, indoor_c: float) -> float:
    """Never allow a negative cooling delta-T to create a cooling load."""
    return max(0.0, outdoor_c - indoor_c)


# n50 (air changes per hour at 50 Pa pressurization test, EN 13829) -> natural
# infiltration ACH under normal weather. The "divide by N" rule is a widely
# used simplified conversion (CIBSE Guide A / BS 5925, popularized as the
# LBL "divide-by-20" shielding-class method): N depends on how sheltered the
# building is from wind, since wind-driven pressure is what turns an
# airtightness test result into an actual infiltration rate.
#
# This is deliberately NOT a full single/double-flow multi-zone infiltration
# model — it is the one documented, versioned place this conversion happens
# so it is applied identically everywhere instead of being recomputed ad hoc
# (previously duplicated as an inline "* 0.05" in the frontend, GC-COOLING-12).
N50_SHIELDING_DIVISOR = {
    "sheltered": 25.0,
    "normal": 20.0,
    "exposed": 15.0,
    "very_exposed": 12.0,
}
N50_CONVERSION_METHOD = "n50_divide_by_shielding_class_v1"


def ach_from_n50(n50_ach_at_50pa: float, wind_exposure: str = "normal") -> float:
    """Converts a measured/estimated n50 value (vol/h at 50 Pa) into an
    estimated natural infiltration rate (ACH) under normal conditions.

    Returns 0.0 for a non-positive n50 (nothing measured/estimated) rather
    than raising, so callers can freely try this first and fall back to a
    manually entered infiltration_ach.
    """
    if n50_ach_at_50pa <= 0:
        return 0.0
    divisor = N50_SHIELDING_DIVISOR.get(wind_exposure, N50_SHIELDING_DIVISOR["normal"])
    return n50_ach_at_50pa / divisor
