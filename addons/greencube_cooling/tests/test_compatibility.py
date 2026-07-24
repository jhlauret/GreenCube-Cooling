# -*- coding: utf-8 -*-
import os
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.compatibility import ProductTechnicalData, assess_compatibility, recommendation_sort_key
else:
    from ..services.compatibility import ProductTechnicalData, assess_compatibility, recommendation_sort_key

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

    # -- GC-COOLING-18: missing-data must never be silently coerced into a
    # capacity/oversizing_ratio of 0.0 (that used to sort as "best fit"). --

    def test_missing_capacity_is_insufficient_data_not_incompatible(self):
        product = ProductTechnicalData(capacity_at_45c_w=None, max_outdoor_temperature_c=46, shr=0.8)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "insufficient_data")
        self.assertIsNone(result.oversizing_ratio)
        self.assertIn("capacity_at_45c_w", result.missing_fields)

    def test_zero_capacity_is_treated_as_missing(self):
        product = ProductTechnicalData(capacity_at_45c_w=0, max_outdoor_temperature_c=46, shr=0.8)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "insufficient_data")

    def test_missing_max_outdoor_temperature_is_insufficient_data(self):
        product = ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=None, shr=0.8)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "insufficient_data")
        self.assertIn("max_outdoor_temperature_c", result.missing_fields)

    def test_missing_shr_is_insufficient_data(self):
        product = ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=46, shr=None)
        result = assess_compatibility(product, recommended_load_w=2000, governing_shr=0.8)
        self.assertEqual(result.status, "insufficient_data")

    def test_zero_recommended_load_is_insufficient_data(self):
        product = ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=46, shr=0.8)
        result = assess_compatibility(product, recommended_load_w=0, governing_shr=0.8)
        self.assertEqual(result.status, "insufficient_data")
        self.assertIsNone(result.oversizing_ratio)

    def test_sort_key_ranks_recommended_before_missing_data_and_incompatible(self):
        recommended = assess_compatibility(
            ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=46, shr=0.8), 2000, 0.8
        )
        missing = assess_compatibility(
            ProductTechnicalData(capacity_at_45c_w=None, max_outdoor_temperature_c=46, shr=0.8), 2000, 0.8
        )
        incompatible = assess_compatibility(
            ProductTechnicalData(capacity_at_45c_w=500, max_outdoor_temperature_c=46, shr=0.8), 2000, 0.8
        )
        ranked = sorted(
            [(incompatible, 3), (missing, 2), (recommended, 1)],
            key=lambda pair: recommendation_sort_key(pair[0], pair[1]),
        )
        self.assertEqual([tie for _assessment, tie in ranked], [1, 2, 3])

    def test_sort_key_is_stable_via_tie_breaker(self):
        a = assess_compatibility(
            ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=46, shr=0.8), 2000, 0.8
        )
        b = assess_compatibility(
            ProductTechnicalData(capacity_at_45c_w=2200, max_outdoor_temperature_c=46, shr=0.8), 2000, 0.8
        )
        # Identical assessments differ only by the tie-breaker (e.g. product id).
        self.assertLess(recommendation_sort_key(a, 10), recommendation_sort_key(b, 20))


if __name__ == "__main__":
    unittest.main()
