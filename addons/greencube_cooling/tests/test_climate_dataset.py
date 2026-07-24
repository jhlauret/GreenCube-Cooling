# -*- coding: utf-8 -*-
"""TransactionCase tests for greencube.cooling.climate.dataset (GC-COOLING-04).

Covers the ORM-dependent parts of the climate cache: cache hit/miss,
immutable-on-refresh (archive + new row, never write() on an existing
payload), checksum reproducibility, and a provider/schema version bump
forcing a brand-new dataset instead of reinterpreting an old cache row.

No network access: `services.climate.build_climate_scenarios` is
monkeypatched with a fixed deterministic fixture for the duration of each
test.
"""
from odoo.tests.common import TransactionCase, tagged

from ..services import climate as climate_service


def _fixed_result(sample_days=120, data_start="2015-06-01", data_end="2024-09-30"):
    return {
        "scenarios": [
            {
                "code": "reference_summer",
                "outdoor_temperature_c": 32.0,
                "outdoor_relative_humidity_percent": 45,
                "wind_speed_ms": 2.0,
                "shortwave_radiation_sum_mj_m2": 20.0,
                "ground_temperature_c": 19.0,
                "reference_date": "2022-07-14",
            },
            {
                "code": "hot_weather",
                "outdoor_temperature_c": 36.0,
                "outdoor_relative_humidity_percent": 38,
                "wind_speed_ms": 1.5,
                "shortwave_radiation_sum_mj_m2": 23.0,
                "ground_temperature_c": 20.0,
                "reference_date": "2019-08-02",
            },
            {
                "code": "prolonged_heatwave",
                "outdoor_temperature_c": 41.0,
                "outdoor_relative_humidity_percent": 30,
                "wind_speed_ms": 1.0,
                "shortwave_radiation_sum_mj_m2": 25.0,
                "ground_temperature_c": 22.0,
                "reference_date": "2023-08-19",
            },
        ],
        "sample_days": sample_days,
        "data_start": data_start,
        "data_end": data_end,
        "provider_code": climate_service.PROVIDER_CODE,
        "provider_version": climate_service.PROVIDER_VERSION,
        "schema_version": climate_service.SCHEMA_VERSION,
        "dataset_type": "historical_observed",
        "license": climate_service.PROVIDER_LICENSE,
        "timezone": "Europe/Paris",
        "variables": ["relative_humidity_2m_mean", "shortwave_radiation_sum"],
    }


@tagged("post_install", "-at_install")
class TestClimateDataset(TransactionCase):
    def setUp(self):
        super().setUp()
        self._orig_build = climate_service.build_climate_scenarios
        self.addCleanup(self._restore_build)
        climate_service.build_climate_scenarios = lambda lat, lon, environment_type=None: _fixed_result()
        self.Dataset = self.env["greencube.cooling.climate.dataset"]

    def _restore_build(self):
        climate_service.build_climate_scenarios = self._orig_build

    def test_cache_miss_creates_dataset(self):
        before = self.Dataset.search_count([])
        payload = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        after = self.Dataset.search_count([])
        self.assertEqual(after, before + 1)
        self.assertTrue(payload["dataset_id"])
        self.assertEqual(payload["dataset_type"], "historical_observed")
        self.assertTrue(payload["checksum"])

    def test_cache_hit_reuses_same_dataset_and_checksum(self):
        first = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        before = self.Dataset.search_count([])
        second = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        after = self.Dataset.search_count([])
        self.assertEqual(before, after, "A cache hit must not create a new row")
        self.assertEqual(first["dataset_id"], second["dataset_id"])
        self.assertEqual(first["checksum"], second["checksum"])

    def test_checksum_reproducible_across_two_locations_same_payload(self):
        """Same fixed provider result -> same checksum, independent of which
        lat/lon triggered the fetch (the checksum is over the payload, not
        the cache key)."""
        first = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        second = self.Dataset.get_or_fetch_scenarios(10.0, 20.0, "suburban")
        self.assertEqual(first["checksum"], second["checksum"])

    def test_stale_cache_is_archived_not_overwritten(self):
        first = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        old_record = self.Dataset.browse(first["dataset_id"])
        old_payload_json = old_record.payload_json
        old_checksum = old_record.checksum

        # Force staleness by rewinding fetched_epoch beyond the TTL — this is
        # the *test* directly manipulating the clock signal, not the model
        # mutating its own payload; the model itself still never write()s
        # payload/checksum on an existing row (asserted below).
        old_record.write({"fetched_epoch": old_record.fetched_epoch - 91 * 24 * 3600})

        second = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")

        old_record.invalidate_recordset()
        self.assertNotEqual(first["dataset_id"], second["dataset_id"], "A stale refresh must create a new dataset row")
        self.assertFalse(old_record.active, "The stale row must be archived, not deleted or reused")
        self.assertEqual(old_record.superseded_by_id.id, second["dataset_id"])
        # The old row's own payload/checksum must be untouched by the refresh.
        self.assertEqual(old_record.payload_json, old_payload_json)
        self.assertEqual(old_record.checksum, old_checksum)

    def test_provider_version_bump_forces_new_dataset(self):
        first = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        original_version = climate_service.PROVIDER_VERSION
        try:
            climate_service.PROVIDER_VERSION = "archive_v2"
            second = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        finally:
            climate_service.PROVIDER_VERSION = original_version
        self.assertNotEqual(
            first["dataset_id"], second["dataset_id"], "A provider_version bump must never reuse an old cache row"
        )

    def test_dataset_type_defaults_to_historical_observed(self):
        payload = self.Dataset.get_or_fetch_scenarios(43.6, 3.9, "suburban")
        record = self.Dataset.browse(payload["dataset_id"])
        self.assertEqual(record.dataset_type, "historical_observed")
        self.assertEqual(record.provider_code, "open_meteo")
