# -*- coding: utf-8 -*-
"""Historical climate service for GC-COOLING-04.

Replaces the fixed altitude-based heuristic with real historical daily
weather pulled from Open-Meteo's free archive API (ERA5 reanalysis, no API
key, ~10 years of daily data in one call). Three dimensioning scenarios are
derived from percentiles of the actual warm-season record for the site
instead of made-up deltas:

- reference_summer: a typical hot day (90th percentile of warm-season daily max)
- hot_weather: a strong heat event (98th percentile)
- prolonged_heatwave: the most extreme observed day (max), used as the
  upper-bound dimensioning scenario

Humidity and wind for each scenario are read from the actual day whose max
temperature is closest to the target percentile, rather than being
independently estimated, so the triplet of (temperature, humidity, wind)
stays physically consistent with a real observed day.
"""
import logging
import statistics
from datetime import date

import requests

_logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEOUT_S = 20
HISTORY_YEARS = 10
DAILY_VARS = (
    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
    "relative_humidity_2m_mean,shortwave_radiation_sum,windspeed_10m_max"
)

SCENARIO_PERCENTILES = {
    "reference_summer": 0.90,
    "hot_weather": 0.98,
}

# --- Provenance / governance constants (GC-COOLING-04) ----------------------
#
# Every value the solver ever sees must be traceable to a provider, a
# version and a dataset type. Bump PROVIDER_VERSION or SCHEMA_VERSION
# whenever the request shape, the variable list or the returned payload
# shape changes — `climate.dataset.get_or_fetch_scenarios()` folds these
# into its cache key so a version bump always produces a *new* dataset
# record instead of silently reinterpreting old cached rows under a new
# meaning.
PROVIDER_CODE = "open_meteo"
PROVIDER_VERSION = "archive_v1"
SCHEMA_VERSION = 1
PROVIDER_LICENSE = "Open-Meteo archive API (ERA5/ERA5-Land reanalysis), CC-BY 4.0"

# This service only ever derives scenarios from *observed* history (daily
# ERA5 reanalysis for years already in the past). It never calls a
# prospective/forward-looking climate model, so the only honest dataset
# type it can ever produce today is `historical_observed`. A real
# `projection` type (CMIP6/CORDEX or similar) would need its own provider
# and its own explicit feature flag — see README_GC-COOLING-04 "Ne pas
# appeler <<projection>> une extrapolation non issue d'un jeu de données
# prospectif reconnu."
DATASET_TYPE_HISTORICAL_OBSERVED = "historical_observed"


class ClimateServiceError(Exception):
    """Raised when the historical weather provider cannot be reached or
    returns unusable data. Callers should fall back to a conservative
    reference heuristic rather than block a calculation on a network hiccup."""


def _warm_season_months(latitude):
    """Northern hemisphere: Jun-Sep. Southern hemisphere: Dec-Mar."""
    if latitude >= 0:
        return {6, 7, 8, 9}
    return {12, 1, 2, 3}


def _percentile(sorted_values, fraction):
    if not sorted_values:
        raise ClimateServiceError("No historical samples available for percentile computation.")
    idx = min(len(sorted_values) - 1, max(0, round(fraction * (len(sorted_values) - 1))))
    return sorted_values[idx]


def fetch_historical_daily(latitude, longitude, years=HISTORY_YEARS):
    """Fetch `years` of daily historical weather ending yesterday (archive
    data typically lags a few days behind real time)."""
    end = date.today().replace(day=1)
    start = end.replace(year=end.year - years)
    try:
        response = requests.get(
            ARCHIVE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "daily": DAILY_VARS,
                "timezone": "auto",
            },
            timeout=TIMEOUT_S,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise ClimateServiceError(f"Historical climate provider unreachable: {exc}") from exc

    daily = data.get("daily")
    if not daily or not daily.get("time"):
        raise ClimateServiceError("Historical climate provider returned no data for this location.")
    # Open-Meteo resolves `timezone=auto` server-side and echoes the actual
    # IANA zone it used for the returned local dates — captured so the
    # dataset can honestly state which timezone its daily boundaries (and
    # therefore its scenario dates) are expressed in (GC-COOLING-04
    # "Conserver ... fuseau IANA").
    daily["_resolved_timezone"] = data.get("timezone") or "UTC"
    return daily


def _closest_day(daily, target_index_in_season, warm_indices, target_tmax):
    """Find the warm-season day whose tmax is closest to target_tmax, returning
    its (humidity, wind) pair so the scenario stays internally consistent."""
    best_i, best_diff = None, None
    for i in warm_indices:
        tmax = daily["temperature_2m_max"][i]
        if tmax is None:
            continue
        diff = abs(tmax - target_tmax)
        if best_diff is None or diff < best_diff:
            best_i, best_diff = i, diff
    if best_i is None:
        raise ClimateServiceError("Could not match a historical day to the requested percentile.")
    return best_i


def build_climate_scenarios(latitude, longitude, environment_type=None):
    """Return the three dimensioning scenarios (reference_summer, hot_weather,
    prolonged_heatwave) derived from real historical data for this location.

    Each entry: code, label, outdoor_temperature_c, outdoor_relative_humidity_percent,
    wind_speed_ms, ground_temperature_c, sample_days, data_start, data_end.
    """
    daily = fetch_historical_daily(latitude, longitude)
    warm_months = _warm_season_months(latitude)
    warm_indices = [
        i for i, t in enumerate(daily["time"]) if int(t.split("-")[1]) in warm_months and daily["temperature_2m_max"][i] is not None
    ]
    if len(warm_indices) < 30:
        raise ClimateServiceError("Not enough warm-season historical samples for this location.")

    warm_tmax_sorted = sorted(daily["temperature_2m_max"][i] for i in warm_indices)
    annual_means = [t for t in daily["temperature_2m_mean"] if t is not None]
    ground_temperature_c = round(statistics.fmean(annual_means), 1) if annual_means else 18.0

    scenarios = []
    for code, fraction in SCENARIO_PERCENTILES.items():
        target_tmax = _percentile(warm_tmax_sorted, fraction)
        day_index = _closest_day(daily, None, warm_indices, target_tmax)
        scenarios.append(
            {
                "code": code,
                "outdoor_temperature_c": round(daily["temperature_2m_max"][day_index], 1),
                "outdoor_relative_humidity_percent": round(daily["relative_humidity_2m_mean"][day_index] or 45, 0),
                "wind_speed_ms": round((daily["windspeed_10m_max"][day_index] or 10) / 3.6, 1),
                "shortwave_radiation_sum_mj_m2": daily["shortwave_radiation_sum"][day_index],
                "ground_temperature_c": ground_temperature_c,
                "reference_date": daily["time"][day_index],
            }
        )

    hottest_index = max(warm_indices, key=lambda i: daily["temperature_2m_max"][i])
    scenarios.append(
        {
            "code": "prolonged_heatwave",
            "outdoor_temperature_c": round(daily["temperature_2m_max"][hottest_index], 1),
            "outdoor_relative_humidity_percent": round(daily["relative_humidity_2m_mean"][hottest_index] or 35, 0),
            "wind_speed_ms": round((daily["windspeed_10m_max"][hottest_index] or 6) / 3.6, 1),
            "shortwave_radiation_sum_mj_m2": daily["shortwave_radiation_sum"][hottest_index],
            "ground_temperature_c": ground_temperature_c + 2,
            "reference_date": daily["time"][hottest_index],
        }
    )

    return {
        "scenarios": scenarios,
        "sample_days": len(warm_indices),
        "data_start": daily["time"][0],
        "data_end": daily["time"][-1],
        # Governance/provenance metadata (GC-COOLING-04): every dataset
        # persisted by climate.dataset carries these so a calculation can
        # always answer "which provider, which version, which period, which
        # timezone, under which license produced this number".
        "provider_code": PROVIDER_CODE,
        "provider_version": PROVIDER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "dataset_type": DATASET_TYPE_HISTORICAL_OBSERVED,
        "license": PROVIDER_LICENSE,
        "timezone": daily.get("_resolved_timezone", "UTC"),
        "variables": sorted(DAILY_VARS.split(",")),
    }


def radiation_wm2_from_daily_sum(shortwave_radiation_sum_mj_m2, daylight_seconds=43200):
    """Rough conversion of a daily shortwave radiation total (MJ/m^2) into an
    indicative peak irradiance (W/m^2), used only to scale the fixed
    facade-orientation distribution — not a substitute for a real hourly
    irradiance model (that level of detail belongs to the Honeybee/EnergyPlus
    path, GC-COOLING-15)."""
    if not shortwave_radiation_sum_mj_m2:
        return 400.0
    return round((shortwave_radiation_sum_mj_m2 * 1_000_000) / daylight_seconds, 0)
