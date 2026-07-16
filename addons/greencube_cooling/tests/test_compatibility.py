# -*- coding: utf-8 -*-
import os
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.compatibility import ProductTechnicalData, assess_compatibility
else:
    from ..services.compatibility import ProductTechnicalData, assess_compatibility

try:
    from odoo.tests.common import BaseCase as _TestCase
except ImportError:
    _TestCase = unittest.TestCase


class CompatibilityTestCase(_TestCase):
    def test_insufficient_capacity_is_incompatible(self):
        product = ProductTechnicalData(capacity_at_45c_w=1000, max_outdoor_temperature_c=46, shr=0.75)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "incompatible")

    def test_low_max_outdoor_temperature_is_incompatible(self):
        product = ProductTechnicalData(capacity_at_45c_w=3000, max_outdoor_temperature_c=38, shr=0.75)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "incompatible")

    def test_well_matched_capacity_is_recommended(self):
        product = ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=46, shr=0.8)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "recommended")

    def test_gross_oversizing_is_not_recommended(self):
        product = ProductTechnicalData(capacity_at_45c_w=5000, max_outdoor_temperature_c=46, shr=0.8)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "not_recommended")

    def test_shr_mismatch_is_compatible_with_conditions(self):
        product = ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=46, shr=0.5)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.85)
        self.assertEqual(result.status, "compatible_with_conditions")


if __name__ == "__main__":
    unittest.main()
