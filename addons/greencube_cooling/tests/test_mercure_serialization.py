# -*- coding: utf-8 -*-
"""Round-trip tests for services/mercure/serialization.py (GC-COOLING-13).

No Odoo dependency: importable and runnable standalone, and through Odoo's
own test runner once the module is installed (see test_mercure_engine.py
for why BaseCase is used when available).
"""
import os
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.mercure.fixtures import studio_standard_input, west_glazed_office_input
    from services.mercure.serialization import mercure_input_from_dict, mercure_input_to_dict
else:
    from ..services.mercure.fixtures import studio_standard_input, west_glazed_office_input
    from ..services.mercure.serialization import mercure_input_from_dict, mercure_input_to_dict

try:
    from odoo.tests.common import BaseCase as _TestCase
except ImportError:
    _TestCase = unittest.TestCase


class MercureSerializationTestCase(_TestCase):
    def test_round_trip_preserves_studio_input(self):
        original = studio_standard_input()
        restored = mercure_input_from_dict(mercure_input_to_dict(original))
        self.assertEqual(original, restored)

    def test_round_trip_preserves_west_glazed_office_input(self):
        original = west_glazed_office_input()
        restored = mercure_input_from_dict(mercure_input_to_dict(original))
        self.assertEqual(original, restored)

    def test_to_dict_is_json_serializable(self):
        import json

        payload = mercure_input_to_dict(studio_standard_input())
        json.dumps(payload, default=str)  # must not raise


if __name__ == "__main__":
    unittest.main()
