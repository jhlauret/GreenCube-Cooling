# -*- coding: utf-8 -*-
"""Pure-Python tests for services/energyplus.py (GC-COOLING-05A).

No Odoo dependency: importable and runnable standalone via
    python3 -m unittest discover -s addons/greencube_cooling/tests
as well as through Odoo's own test runner once the module is installed.

These tests are the ones the condensed GC-COOLING-05A spec explicitly
requires and that were previously missing entirely: feature-flag
on/off behaviour, "dependencies absent" raising a clear/explicit error,
and (only if the environment genuinely has the stack) exercising the
real availability/compatibility check instead of assuming it passed.
"""
import os
import sys
import unittest
from unittest import mock

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services import energyplus
    from services.mercure.fixtures import studio_standard_input
else:
    from ..services import energyplus
    from ..services.mercure.fixtures import studio_standard_input


class _EnvVarGuard:
    """Saves/restores os.environ around a test that needs to set/unset a
    specific variable, without leaking state into other tests."""

    def __init__(self, **overrides):
        self._overrides = overrides
        self._backup = None

    def __enter__(self):
        self._backup = dict(os.environ)
        for key, value in self._overrides.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return self

    def __exit__(self, *exc_info):
        os.environ.clear()
        os.environ.update(self._backup)


class IsEnergyplusEnabledTestCase(unittest.TestCase):
    def test_default_is_disabled(self):
        with _EnvVarGuard(GC_COOLING_ENERGYPLUS_ENABLED=None):
            self.assertFalse(energyplus.is_energyplus_enabled())

    def test_explicit_false_is_disabled(self):
        with _EnvVarGuard(GC_COOLING_ENERGYPLUS_ENABLED="false"):
            self.assertFalse(energyplus.is_energyplus_enabled())

    def test_truthy_values_enable_it(self):
        for value in ("1", "true", "True", "yes", "YES"):
            with _EnvVarGuard(GC_COOLING_ENERGYPLUS_ENABLED=value):
                self.assertTrue(energyplus.is_energyplus_enabled(), msg=f"value={value!r}")

    def test_garbage_value_is_disabled(self):
        with _EnvVarGuard(GC_COOLING_ENERGYPLUS_ENABLED="maybe"):
            self.assertFalse(energyplus.is_energyplus_enabled())


class CheckAvailabilityTestCase(unittest.TestCase):
    def test_reports_unavailable_when_stack_is_missing(self):
        # This sandbox genuinely has none of honeybee-energy/ladybug/an
        # EnergyPlus binary installed (see the module's own docstring) —
        # proving this against the real function, not a mock, is the
        # whole point of GC-COOLING-05A pt.3's "never declare EnergyPlus
        # operational without a real test" rule.
        available, detail = energyplus.check_availability()
        self.assertFalse(available)
        self.assertIn("Missing", detail)

    def test_get_component_versions_reports_none_for_absent_components(self):
        versions = energyplus.get_component_versions()
        self.assertIsNone(versions["honeybee_energy"])
        self.assertIsNone(versions["ladybug"])
        self.assertIsNone(versions["energyplus"])

    def test_check_compatibility_reports_unknown_for_absent_components(self):
        matrix = energyplus.check_compatibility({"honeybee_energy": None, "ladybug": None, "energyplus": None, "openstudio": None})
        for component, info in matrix.items():
            self.assertIsNone(info["compatible"], msg=component)
            self.assertIsNone(info["detected"], msg=component)
            self.assertTrue(info["expected"])

    def test_check_compatibility_flags_pinned_version_as_compatible(self):
        matrix = energyplus.check_compatibility(
            {
                "honeybee_energy": energyplus.COMPATIBLE_HONEYBEE_ENERGY_VERSION,
                "ladybug": energyplus.COMPATIBLE_LADYBUG_VERSION,
                "energyplus": f"EnergyPlus, Version {energyplus.COMPATIBLE_ENERGYPLUS_VERSION}-abc123",
                "openstudio": energyplus.COMPATIBLE_OPENSTUDIO_VERSION,
            }
        )
        self.assertTrue(matrix["honeybee_energy"]["compatible"])
        self.assertTrue(matrix["ladybug"]["compatible"])
        self.assertTrue(matrix["energyplus"]["compatible"])
        self.assertTrue(matrix["openstudio"]["compatible"])

    def test_check_compatibility_flags_mismatched_version_as_incompatible(self):
        matrix = energyplus.check_compatibility({"honeybee_energy": "0.1.0", "ladybug": None, "energyplus": None, "openstudio": None})
        self.assertFalse(matrix["honeybee_energy"]["compatible"])

    def test_availability_surfaces_unpinned_version_warning_when_present(self):
        # Simulate every dependency being "present" but on an unpinned
        # version, without needing the real packages installed here.
        fake_versions = {
            "honeybee_energy": "9.9.9",
            "ladybug": "9.9.9",
            "energyplus": "EnergyPlus, Version 9.9.9",
            "openstudio": None,
        }
        with mock.patch.object(energyplus, "get_component_versions", return_value=fake_versions), \
             mock.patch.object(energyplus.shutil, "which", return_value="/usr/bin/energyplus"):
            available, detail = energyplus.check_availability()
        self.assertTrue(available)
        self.assertIn("UNPINNED VERSION WARNING", detail)


class RunEnergyplusSimulationTestCase(unittest.TestCase):
    def test_raises_explicit_unavailable_error_when_stack_missing(self):
        mercure_input = studio_standard_input()
        with self.assertRaises(energyplus.EnergyPlusUnavailableError) as ctx:
            energyplus.run_energyplus_simulation(mercure_input)
        self.assertIn("not installed", str(ctx.exception))

    def test_raises_simulation_error_not_unavailable_once_stack_present(self):
        # Proves the two error types stay distinct: once the (mocked, since
        # not actually installed here) stack reports available, the
        # function must fail with "not implemented yet"
        # (EnergyPlusSimulationError), never silently succeed and never
        # raise the "unavailable" error instead.
        mercure_input = studio_standard_input()
        with mock.patch.object(energyplus, "check_availability", return_value=(True, "mocked as present")):
            with self.assertRaises(energyplus.EnergyPlusSimulationError) as ctx:
                energyplus.run_energyplus_simulation(mercure_input)
        self.assertIn("not implemented", str(ctx.exception))


@unittest.skipUnless(
    __import__("importlib").util.find_spec("honeybee_energy") is not None,
    "honeybee-energy is not installed in this environment: GC-COOLING-05A pt.3 forbids declaring "
    "a real Honeybee model validation passed without the library actually available to run it.",
)
class RealHoneybeeValidationTestCase(unittest.TestCase):  # pragma: no cover - only runs if honeybee-energy is present
    def test_real_honeybee_model_validates(self):
        # Intentionally not implemented against a mock: if this ever runs,
        # it must exercise the real honeybee_energy validation API, not a
        # stand-in. Since the package is absent from this repo's tested
        # environments today, this test is skipped rather than faked.
        self.skipTest("No real honeybee-energy Model-construction path is implemented yet (GC-COOLING-15 scope).")


if __name__ == "__main__":
    unittest.main()
