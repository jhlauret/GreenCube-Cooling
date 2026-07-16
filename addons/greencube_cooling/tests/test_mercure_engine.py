# -*- coding: utf-8 -*-
"""Unit tests for the MERCURE engine.

No Odoo dependency: importable and runnable standalone via
    python3 -m unittest discover -s addons/greencube_cooling/tests
as well as through Odoo's own test runner once the module is installed.
"""
import dataclasses
import os
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.mercure.conversions import ach_to_m3h, positive_cooling_delta_t, watts_to_btu_per_hour, watts_to_kw
    from services.mercure.engine import MercureError, run_mercure
    from services.mercure.fixtures import studio_standard_input, west_glazed_office_input
else:
    from ..services.mercure.conversions import ach_to_m3h, positive_cooling_delta_t, watts_to_btu_per_hour, watts_to_kw
    from ..services.mercure.engine import MercureError, run_mercure
    from ..services.mercure.fixtures import studio_standard_input, west_glazed_office_input


class ConversionsTestCase(unittest.TestCase):
    def test_watts_to_kw(self):
        self.assertAlmostEqual(watts_to_kw(1500), 1.5)

    def test_watts_to_btu_per_hour(self):
        self.assertAlmostEqual(watts_to_btu_per_hour(1000), 3412.14, places=1)

    def test_ach_to_m3h(self):
        self.assertAlmostEqual(ach_to_m3h(0.6, 78), 46.8)

    def test_positive_cooling_delta_t_clamps_negative(self):
        self.assertEqual(positive_cooling_delta_t(20, 25), 0)
        self.assertEqual(positive_cooling_delta_t(30, 25), 5)


def _breakdown_value(scenario_result, code, field="total_w"):
    for entry in scenario_result.breakdown:
        if entry.component_code == code:
            return getattr(entry, field)
    raise KeyError(code)


class ReferenceCasesTestCase(unittest.TestCase):
    def test_standard_studio_produces_complete_result(self):
        result = run_mercure(studio_standard_input())
        self.assertEqual(len(result.scenario_results), 3)
        self.assertGreater(result.recommended_capacity_w, 0)
        self.assertAlmostEqual(result.recommended_capacity_kw, result.recommended_capacity_w / 1000)
        self.assertEqual(result.governing_scenario_code, "prolonged_heatwave")
        for scenario in result.scenario_results:
            self.assertGreaterEqual(scenario.total_load_w, scenario.sensible_load_w)
            self.assertGreater(scenario.shr, 0)
            self.assertLessEqual(scenario.shr, 1)

    def test_total_load_never_below_sensible(self):
        result = run_mercure(west_glazed_office_input())
        for scenario in result.scenario_results:
            self.assertGreaterEqual(scenario.total_load_w, scenario.sensible_load_w)


class MonotonicPropertiesTestCase(unittest.TestCase):
    def test_more_glazing_area_does_not_reduce_solar_gain(self):
        base = studio_standard_input()
        more = dataclasses.replace(
            base,
            glazing=dataclasses.replace(base.glazing, facades=[dataclasses.replace(f, area_m2=f.area_m2 * 2) for f in base.glazing.facades]),
        )
        base_result = run_mercure(base).scenario_results[0]
        more_result = run_mercure(more).scenario_results[0]
        self.assertGreaterEqual(
            _breakdown_value(more_result, "solar_glazing"),
            _breakdown_value(base_result, "solar_glazing"),
        )

    def test_more_occupants_does_not_reduce_human_gains(self):
        base = studio_standard_input()
        more = dataclasses.replace(base, occupancy=dataclasses.replace(base.occupancy, usual_occupants=base.occupancy.usual_occupants + 2))
        base_result = run_mercure(base).scenario_results[0]
        more_result = run_mercure(more).scenario_results[0]
        self.assertGreater(
            _breakdown_value(more_result, "occupants_sensible"),
            _breakdown_value(base_result, "occupants_sensible"),
        )

    def test_hotter_outdoor_air_does_not_reduce_ventilation_load(self):
        base = studio_standard_input()
        hotter = dataclasses.replace(
            base,
            climate_scenarios=[dataclasses.replace(s, outdoor_temperature_c=s.outdoor_temperature_c + 5) for s in base.climate_scenarios],
        )
        base_result = run_mercure(base).scenario_results[0]
        hotter_result = run_mercure(hotter).scenario_results[0]
        self.assertGreaterEqual(
            _breakdown_value(hotter_result, "ventilation_sensible"),
            _breakdown_value(base_result, "ventilation_sensible"),
        )

    def test_better_heat_recovery_does_not_increase_ventilation_load(self):
        base = studio_standard_input()
        better = dataclasses.replace(base, ventilation=dataclasses.replace(base.ventilation, heat_recovery_efficiency=0.8))
        base_result = run_mercure(base).scenario_results[0]
        better_result = run_mercure(better).scenario_results[0]
        self.assertLessEqual(
            _breakdown_value(better_result, "ventilation_sensible"),
            _breakdown_value(base_result, "ventilation_sensible"),
        )

    def test_higher_setpoint_does_not_increase_transmission_load(self):
        base = studio_standard_input()
        higher = dataclasses.replace(base, comfort=dataclasses.replace(base.comfort, cooling_setpoint_day_c=base.comfort.cooling_setpoint_day_c + 2))
        base_result = run_mercure(base).scenario_results[0]
        higher_result = run_mercure(higher).scenario_results[0]
        self.assertLessEqual(
            _breakdown_value(higher_result, "envelope_walls"),
            _breakdown_value(base_result, "envelope_walls"),
        )


class ErrorsTestCase(unittest.TestCase):
    def test_rejects_snapshot_without_climate_scenarios(self):
        base = studio_standard_input()
        invalid = dataclasses.replace(base, climate_scenarios=[])
        with self.assertRaises(MercureError):
            run_mercure(invalid)

    def test_rejects_invalid_geometry(self):
        base = studio_standard_input()
        invalid = dataclasses.replace(base, geometry=dataclasses.replace(base.geometry, floor_area_m2=0))
        with self.assertRaises(MercureError):
            run_mercure(invalid)


if __name__ == "__main__":
    unittest.main()
