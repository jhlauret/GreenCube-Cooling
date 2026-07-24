# -*- coding: utf-8 -*-
"""Unit tests for the historical climate service (GC-COOLING-04).

No Odoo dependency, no network access: `fetch_historical_daily` is
monkeypatched with a fixed, deterministic fixture (a synthetic ~2-year
daily series with a clear warm season) so these tests run fully offline,
following the same standalone-or-Odoo-runnable pattern as
test_mercure_engine.py.
"""
import os
import sys
import unittest
from datetime import date, timedelta

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services import climate as climate_service
else:
    from ..services import climate as climate_service

try:
    from odoo.tests.common import BaseCase as _TestCase
except ImportError:
    _TestCase = unittest.TestCase


def _synthetic_daily_fixture(years=3, warm_base=30.0, cold_base=8.0):
    """Deterministic two-and-a-bit-year daily series: Jun-Sep is "warm
    season" with a slow ramp so percentiles are unambiguous, the rest of
    the year is a flat cold baseline. No randomness anywhere, so two calls
    with this fixture always produce byte-identical output."""
    start = date(2021, 1, 1)
    days = 365 * years
    time_, tmax, tmin, tmean, rh, rad, wind = [], [], [], [], [], [], []
    for i in range(days):
        d = start + timedelta(days=i)
        time_.append(d.isoformat())
        if d.month in (6, 7, 8, 9):
            # Ramps 0..~45 across the warm season of a given year so the
            # sorted percentile has many distinct candidate values.
            day_in_season = (d - date(d.year, 6, 1)).days
            t = warm_base + (day_in_season % 46)
            rh.append(35.0 + (day_in_season % 10))
            rad.append(18.0 + (day_in_season % 6))
            wind.append(10.0 + (day_in_season % 4))
        else:
            t = cold_base
            rh.append(70.0)
            rad.append(4.0)
            wind.append(15.0)
        tmax.append(round(t, 1))
        tmin.append(round(t - 8, 1))
        tmean.append(round(t - 4, 1))
    return {
        "time": time_,
        "temperature_2m_max": tmax,
        "temperature_2m_min": tmin,
        "temperature_2m_mean": tmean,
        "relative_humidity_2m_mean": rh,
        "shortwave_radiation_sum": rad,
        "windspeed_10m_max": wind,
        "_resolved_timezone": "Europe/Paris",
    }


class ClimateServiceTestCase(_TestCase):
    def setUp(self):
        super().setUp()
        self._orig_fetch = climate_service.fetch_historical_daily
        self._fixture = _synthetic_daily_fixture()
        climate_service.fetch_historical_daily = lambda lat, lon, years=climate_service.HISTORY_YEARS: self._fixture

    def tearDown(self):
        climate_service.fetch_historical_daily = self._orig_fetch
        super().tearDown()

    # -- percentile helper ---------------------------------------------
    def test_percentile_empty_raises(self):
        with self.assertRaises(climate_service.ClimateServiceError):
            climate_service._percentile([], 0.9)

    def test_percentile_bounds(self):
        values = list(range(10))
        self.assertEqual(climate_service._percentile(values, 0.0), 0)
        self.assertEqual(climate_service._percentile(values, 1.0), 9)

    # -- warm season definition ------------------------------------------
    def test_warm_season_northern_hemisphere(self):
        self.assertEqual(climate_service._warm_season_months(45.0), {6, 7, 8, 9})

    def test_warm_season_southern_hemisphere(self):
        self.assertEqual(climate_service._warm_season_months(-33.0), {12, 1, 2, 3})

    # -- scenario building -------------------------------------------------
    def test_three_scenarios_produced(self):
        result = climate_service.build_climate_scenarios(48.85, 2.35)
        codes = {s["code"] for s in result["scenarios"]}
        self.assertEqual(codes, {"reference_summer", "hot_weather", "prolonged_heatwave"})

    def test_scenario_ordering_is_physically_consistent(self):
        """hot_weather (P98) must never be cooler than reference_summer (P90),
        and prolonged_heatwave (max) must never be cooler than hot_weather."""
        result = climate_service.build_climate_scenarios(48.85, 2.35)
        by_code = {s["code"]: s for s in result["scenarios"]}
        self.assertLessEqual(
            by_code["reference_summer"]["outdoor_temperature_c"],
            by_code["hot_weather"]["outdoor_temperature_c"],
        )
        self.assertLessEqual(
            by_code["hot_weather"]["outdoor_temperature_c"],
            by_code["prolonged_heatwave"]["outdoor_temperature_c"],
        )

    def test_units_and_provenance_metadata(self):
        result = climate_service.build_climate_scenarios(48.85, 2.35)
        self.assertEqual(result["provider_code"], "open_meteo")
        self.assertEqual(result["provider_version"], climate_service.PROVIDER_VERSION)
        self.assertEqual(result["dataset_type"], "historical_observed")
        self.assertEqual(result["timezone"], "Europe/Paris")
        self.assertIn("relative_humidity_2m", ",".join(result["variables"]))

    def test_not_enough_warm_samples_raises(self):
        # A fixture with no warm months at all (everything is "cold").
        empty_warm = _synthetic_daily_fixture()
        for i, t in enumerate(empty_warm["time"]):
            # Force every date into December so the Jun-Sep filter finds nothing.
            pass
        sparse = {
            "time": ["2021-01-01", "2021-01-02"],
            "temperature_2m_max": [10.0, 11.0],
            "temperature_2m_min": [2.0, 3.0],
            "temperature_2m_mean": [6.0, 7.0],
            "relative_humidity_2m_mean": [60.0, 61.0],
            "shortwave_radiation_sum": [3.0, 3.0],
            "windspeed_10m_max": [10.0, 10.0],
            "_resolved_timezone": "UTC",
        }
        climate_service.fetch_historical_daily = lambda lat, lon, years=climate_service.HISTORY_YEARS: sparse
        with self.assertRaises(climate_service.ClimateServiceError):
            climate_service.build_climate_scenarios(48.85, 2.35)

    # -- reproducibility / checksum ----------------------------------------
    def test_reproducible_checksum_for_same_input(self):
        """Same fixture in -> byte-identical payload out, both calls, so a
        checksum computed over the serialized result is stable (asserted at
        the ORM layer in test_climate_dataset.py; this asserts the
        prerequisite determinism at the pure-function level)."""
        import json

        first = climate_service.build_climate_scenarios(48.85, 2.35)
        second = climate_service.build_climate_scenarios(48.85, 2.35)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    # -- radiation conversion -----------------------------------------------
    def test_radiation_conversion_default_when_missing(self):
        self.assertEqual(climate_service.radiation_wm2_from_daily_sum(None), 400.0)

    def test_radiation_conversion_positive(self):
        value = climate_service.radiation_wm2_from_daily_sum(20.0)
        self.assertGreater(value, 0)


if __name__ == "__main__":
    unittest.main()
