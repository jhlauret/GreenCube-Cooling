# -*- coding: utf-8 -*-
"""
Unit tests for the standalone EnergyPlus worker. Pure Python, no Odoo and
no network — run with `python3 -m unittest energyplus_worker.test_worker`
or `python3 energyplus_worker/test_worker.py` from the repo root.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import worker  # noqa: E402
from addon_bridge import load as load_addon_modules  # noqa: E402


class AddonBridgeTestCase(unittest.TestCase):
    """Proves the bridge actually loads the addon's pure-Python modules —
    the whole point of energyplus_worker existing as a separate process."""

    def test_loads_energyplus_and_mercure_modules(self):
        modules = load_addon_modules()
        self.assertTrue(hasattr(modules.energyplus, "run_energyplus_simulation"))
        self.assertTrue(hasattr(modules.energyplus, "EnergyPlusUnavailableError"))
        self.assertTrue(hasattr(modules.serialization, "mercure_input_from_dict"))
        self.assertTrue(hasattr(modules.fixtures, "studio_standard_input"))

    def test_fixture_round_trips_through_serialization(self):
        modules = load_addon_modules()
        original = modules.fixtures.studio_standard_input()
        as_dict = modules.serialization.mercure_input_to_dict(original)
        json.dumps(as_dict, default=str)  # must be JSON-serializable
        restored = modules.serialization.mercure_input_from_dict(as_dict)
        self.assertEqual(original, restored)

    def test_energyplus_stack_reports_unavailable_without_real_binary(self):
        """This environment (and this MVP's target environment, per
        services/energyplus.py's own docstring) never has honeybee-energy/
        ladybug/an EnergyPlus binary installed — proves the worker's error
        path is exercised against the real function, not a mock."""
        modules = load_addon_modules()
        original = modules.fixtures.studio_standard_input()
        with self.assertRaises(modules.energyplus.EnergyPlusUnavailableError):
            modules.energyplus.run_energyplus_simulation(original)


class BackoffTestCase(unittest.TestCase):
    def test_zero_attempts_means_no_wait(self):
        self.assertEqual(worker.backoff_seconds(0), 0)

    def test_backoff_grows_exponentially(self):
        self.assertEqual(worker.backoff_seconds(1), 2)
        self.assertEqual(worker.backoff_seconds(2), 4)
        self.assertEqual(worker.backoff_seconds(3), 8)

    def test_backoff_is_capped(self):
        self.assertEqual(worker.backoff_seconds(20, max_s=300), 300)


class ClassifyRunResultTestCase(unittest.TestCase):
    def setUp(self):
        self.modules = load_addon_modules()

    def test_no_exception_is_completed(self):
        status, detail = worker.classify_run_result(None, self.modules.energyplus)
        self.assertEqual(status, "simulation_completed")
        self.assertIsNone(detail)

    def test_unavailable_error_maps_to_unavailable(self):
        exc = self.modules.energyplus.EnergyPlusUnavailableError("stack missing")
        status, detail = worker.classify_run_result(exc, self.modules.energyplus)
        self.assertEqual(status, "simulation_unavailable")
        self.assertIn("stack missing", detail)

    def test_simulation_error_maps_to_failed(self):
        exc = self.modules.energyplus.EnergyPlusSimulationError("solver crashed")
        status, detail = worker.classify_run_result(exc, self.modules.energyplus)
        self.assertEqual(status, "simulation_failed")
        self.assertIn("solver crashed", detail)

    def test_unexpected_exception_still_reported_as_failed_not_raised(self):
        status, detail = worker.classify_run_result(ValueError("boom"), self.modules.energyplus)
        self.assertEqual(status, "simulation_failed")
        self.assertIn("boom", detail)


class WorkerConfigTestCase(unittest.TestCase):
    def test_from_env_requires_both_variables(self):
        env_backup = dict(os.environ)
        try:
            os.environ.pop("GC_COOLING_API_BASE_URL", None)
            os.environ.pop("GC_COOLING_ENERGYPLUS_WORKER_KEY", None)
            with self.assertRaises(RuntimeError):
                worker.WorkerConfig.from_env()
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

    def test_from_env_reads_configured_values(self):
        env_backup = dict(os.environ)
        try:
            os.environ["GC_COOLING_API_BASE_URL"] = "http://localhost:8069/"
            os.environ["GC_COOLING_ENERGYPLUS_WORKER_KEY"] = "secret"
            config = worker.WorkerConfig.from_env()
            self.assertEqual(config.api_base_url, "http://localhost:8069")
            self.assertEqual(config.worker_key, "secret")
        finally:
            os.environ.clear()
            os.environ.update(env_backup)


if __name__ == "__main__":
    unittest.main()
