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
