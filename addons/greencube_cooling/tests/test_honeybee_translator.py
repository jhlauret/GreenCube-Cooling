# -*- coding: utf-8 -*-
"""Pure-Python tests for services/mercure/honeybee_translator.py
(GC-COOLING-05A). No Odoo import — runnable in any environment with the
repo on sys.path, same as test_mercure_engine.py/test_mercure_serialization.py.
"""
import dataclasses
import os
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.mercure.fixtures import studio_standard_input, west_glazed_office_input
    from services.mercure.honeybee_translator import HoneybeeTranslationError, build_honeybee_model
else:
    from ..services.mercure.fixtures import studio_standard_input, west_glazed_office_input
    from ..services.mercure.honeybee_translator import HoneybeeTranslationError, build_honeybee_model


class BuildHoneybeeModelTestCase(unittest.TestCase):
    def test_standard_studio_produces_complete_model(self):
        model, diagnostics = build_honeybee_model(studio_standard_input())

        self.assertEqual(model["type"], "Model")
        self.assertEqual(len(model["rooms"]), 1)
        room = model["rooms"][0]
        self.assertEqual(len(room["faces"]), 6)  # 4 walls + roof + floor
        self.assertTrue(diagnostics.checksum_sha256)
        self.assertGreater(len(diagnostics.assumptions), 0)

    def test_glazing_apertures_attach_to_matching_wall(self):
        model, _ = build_honeybee_model(west_glazed_office_input())
        room = model["rooms"][0]
        west_wall = next(f for f in room["faces"] if f["identifier"] == "wall-west")
        self.assertTrue(west_wall["apertures"])
        self.assertGreater(west_wall["apertures"][0]["area_m2"], 0)

    def test_deterministic_checksum(self):
        study_input = studio_standard_input()
        _, diag1 = build_honeybee_model(study_input)
        _, diag2 = build_honeybee_model(study_input)
        self.assertEqual(diag1.checksum_sha256, diag2.checksum_sha256)

    def test_different_snapshots_produce_different_checksums(self):
        _, diag_studio = build_honeybee_model(studio_standard_input())
        _, diag_office = build_honeybee_model(west_glazed_office_input())
        self.assertNotEqual(diag_studio.checksum_sha256, diag_office.checksum_sha256)

    def test_rejects_non_positive_geometry(self):
        study_input = studio_standard_input()
        bad_geometry = dataclasses.replace(study_input.geometry, length_m=0)
        bad_input = dataclasses.replace(study_input, geometry=bad_geometry)
        with self.assertRaises(HoneybeeTranslationError):
            build_honeybee_model(bad_input)

    def test_rejects_glazing_larger_than_wall(self):
        study_input = studio_standard_input()
        oversized_facade = dataclasses.replace(study_input.glazing.facades[0], area_m2=10_000)
        bad_glazing = dataclasses.replace(
            study_input.glazing, facades=[oversized_facade] + list(study_input.glazing.facades[1:])
        )
        bad_input = dataclasses.replace(study_input, glazing=bad_glazing)
        with self.assertRaises(HoneybeeTranslationError):
            build_honeybee_model(bad_input)

    def test_equipment_load_becomes_power_density(self):
        model, _ = build_honeybee_model(studio_standard_input())
        equipment = model["rooms"][0]["properties"]["energy"]["electric_equipment"]
        self.assertGreaterEqual(equipment["watts_per_area"], 0)


if __name__ == "__main__":
    unittest.main()
