# -*- coding: utf-8 -*-
"""Unit tests for the MERCURE engine.

No Odoo dependency: importable and runnable standalone via
    python3 -m unittest discover -s addons/greencube_cooling/tests
as well as through Odoo's own test runner once the module is installed.
"""
import dataclasses
import json
import os
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.mercure.conversions import (
        ach_from_n50,
        ach_to_m3h,
        positive_cooling_delta_t,
        watts_to_btu_per_hour,
        watts_to_kw,
    )
    from services.mercure.engine import MercureError, run_mercure
    from services.mercure.fixtures import studio_standard_input, west_glazed_office_input
else:
    from ..services.mercure.conversions import (
        ach_from_n50,
        ach_to_m3h,
        positive_cooling_delta_t,
        watts_to_btu_per_hour,
        watts_to_kw,
    )
    from ..services.mercure.engine import MercureError, run_mercure
    from ..services.mercure.fixtures import studio_standard_input, west_glazed_office_input

try:
    # Under Odoo's own test runner, deriving from BaseCase (instead of plain
    # unittest.TestCase) lets odoo.tests.common.MetaCase assign the
    # 'test_tags'/'test_module' attributes these tests need to be picked up
    # by --test-tags, while still running with no DB/registry dependency.
    from odoo.tests.common import BaseCase as _TestCase
except ImportError:
    _TestCase = unittest.TestCase


class ConversionsTestCase(_TestCase):
    def test_watts_to_kw(self):
        self.assertAlmostEqual(watts_to_kw(1500), 1.5)

    def test_watts_to_btu_per_hour(self):
        self.assertAlmostEqual(watts_to_btu_per_hour(1000), 3412.14, places=1)

    def test_ach_to_m3h(self):
        self.assertAlmostEqual(ach_to_m3h(0.6, 78), 46.8)

    def test_positive_cooling_delta_t_clamps_negative(self):
        self.assertEqual(positive_cooling_delta_t(20, 25), 0)
        self.assertEqual(positive_cooling_delta_t(30, 25), 5)

    def test_ach_from_n50_zero_is_zero(self):
        self.assertEqual(ach_from_n50(0, "normal"), 0.0)

    def test_ach_from_n50_divide_by_shielding_class(self):
        self.assertAlmostEqual(ach_from_n50(6.0, "normal"), 0.3)
        self.assertAlmostEqual(ach_from_n50(6.0, "sheltered"), 0.24)
        self.assertAlmostEqual(ach_from_n50(6.0, "exposed"), 0.4)

    def test_ach_from_n50_unknown_exposure_falls_back_to_normal(self):
        self.assertAlmostEqual(ach_from_n50(6.0, "not_a_real_exposure"), ach_from_n50(6.0, "normal"))

    def test_ach_from_n50_more_exposed_never_gives_less_infiltration(self):
        sheltered = ach_from_n50(4.0, "sheltered")
        normal = ach_from_n50(4.0, "normal")
        exposed = ach_from_n50(4.0, "exposed")
        self.assertLessEqual(sheltered, normal)
        self.assertLessEqual(normal, exposed)


def _breakdown_value(scenario_result, code, field="total_w"):
    for entry in scenario_result.breakdown:
        if entry.component_code == code:
            return getattr(entry, field)
    raise KeyError(code)


class ReferenceCasesTestCase(_TestCase):
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


class SolarGainByFacadeTestCase(_TestCase):
    """GC-COOLING-09 pt.11: the per-facade decomposition must be an
    informative view of the same solar_glazing total already in
    breakdown, not an extra load, and must actually vary by orientation
    (non-regression for the audit's rotation/orientation fix)."""

    def test_sums_to_the_aggregate_solar_glazing_breakdown_entry(self):
        result = run_mercure(studio_standard_input())
        for scenario in result.scenario_results:
            solar_entry = _breakdown_value(scenario, "solar_glazing")
            self.assertAlmostEqual(
                sum(g.gain_w for g in scenario.solar_gain_by_facade),
                solar_entry,
                places=6,
            )

    def test_one_entry_per_glazed_facade_with_matching_orientation(self):
        result = run_mercure(studio_standard_input())
        scenario = result.scenario_results[0]
        self.assertEqual(len(scenario.solar_gain_by_facade), 1)
        self.assertEqual(scenario.solar_gain_by_facade[0].facade, "south")

    def test_west_glazed_office_shows_west_as_the_dominant_facade(self):
        """A west-glazed office (audit example: 'baie ouest importante')
        must show its solar gain concentrated on the west facade, not
        blended into an orientation-agnostic average."""
        result = run_mercure(west_glazed_office_input())
        scenario = result.scenario_results[0]
        by_facade = {g.facade: g.gain_w for g in scenario.solar_gain_by_facade}
        self.assertIn("west", by_facade)
        self.assertGreater(by_facade["west"], 0)
        self.assertEqual(max(by_facade, key=by_facade.get), "west")


class MonotonicPropertiesTestCase(_TestCase):
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


class DeterminismTestCase(_TestCase):
    """GC-COOLING-14: the same snapshot input must always produce the exact
    same result — no current-time reads, no hidden mutable state, no
    dict/set-ordering nondeterminism."""

    def test_run_mercure_is_deterministic_for_the_same_input(self):
        mercure_input = studio_standard_input()
        first = dataclasses.asdict(run_mercure(mercure_input))
        second = dataclasses.asdict(run_mercure(mercure_input))
        self.assertEqual(first, second)

    def test_run_mercure_does_not_mutate_its_input(self):
        mercure_input = studio_standard_input()
        before = dataclasses.asdict(mercure_input)
        run_mercure(mercure_input)
        after = dataclasses.asdict(mercure_input)
        self.assertEqual(before, after)


class GoldenReferenceConformanceTestCase(_TestCase):
    """GC-COOLING-14 pt.5: numeric conformance fixture shared with the
    TypeScript port (frontend/src/mercure/engine.test.ts reads the same
    JSON file and compares its own output against it within a relative
    tolerance), so the two implementations cannot silently drift apart."""

    RELATIVE_TOLERANCE = 1e-6

    @classmethod
    def _golden(cls):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "mercure_golden_reference.json")
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def _assert_close(self, actual, expected, path):
        if isinstance(expected, dict):
            for key, value in expected.items():
                self._assert_close(actual[key], value, f"{path}.{key}")
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            self.assertAlmostEqual(
                actual, expected, delta=max(abs(expected) * self.RELATIVE_TOLERANCE, 1e-9), msg=path
            )
        else:
            self.assertEqual(actual, expected, path)

    def _summarize(self, result):
        return {
            "engineCode": result.engine_code,
            "engineVersion": result.engine_version,
            "governingScenarioCode": result.governing_scenario_code,
            "recommendedCapacityW": result.recommended_capacity_w,
            "recommendedCapacityKw": result.recommended_capacity_kw,
            "recommendedCapacityBtuH": result.recommended_capacity_btu_h,
            "scenarios": {
                s.scenario_code: {
                    "sensibleLoadW": s.sensible_load_w,
                    "latentLoadW": s.latent_load_w,
                    "totalLoadW": s.total_load_w,
                    "shr": s.shr,
                    "marginW": s.margin_w,
                    "recommendedLoadW": s.recommended_load_w,
                }
                for s in result.scenario_results
            },
        }

    def test_studio_standard_matches_golden_reference(self):
        golden = self._golden()
        actual = self._summarize(run_mercure(studio_standard_input()))
        self._assert_close(actual, golden["studioStandard"], "studioStandard")

    def test_west_glazed_office_matches_golden_reference(self):
        golden = self._golden()
        actual = self._summarize(run_mercure(west_glazed_office_input()))
        self._assert_close(actual, golden["westGlazedOffice"], "westGlazedOffice")


class ErrorsTestCase(_TestCase):
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
