# -*- coding: utf-8 -*-
"""GC-COOLING-03: geolocation, altitude, timezone and location provenance.

Covers, purely through the ORM (no Internet access — `geo_service` calls
are monkeypatched, never left to hit the real Open-Meteo endpoints):
- latitude/longitude/altitude bounds, including the exact-zero case that
  used to be confused with "unset" (audit finding);
- IANA timezone validation;
- the `environment_type` enum and the `urban_dense` -> `dense_urban`
  migration script;
- the geo cache's hit/miss/stale-fallback behaviour and configurable TTL;
- `action_confirm_geolocation()`'s provenance/precision/audit-trail
  bookkeeping, including that a manual correction's provenance survives.

Cross-user API access to a study's location (another user cannot read or
confirm someone else's study's location) is covered in tests/test_http_api.py
alongside the module's other cross-user/cross-company HTTP checks, since it
needs the real HTTP+ir.rule stack that only HttpCase exercises.
"""
import time
from unittest import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..services import geo as geo_service


def _thermal_spec_vals(company_id=False, code="GC-GEO-01"):
    return {
        "name": "Studio geoloc test",
        "code": code,
        "version": "1.0",
        "length_m": 6.0,
        "width_m": 5.0,
        "height_m": 2.6,
        "wall_u_value": 0.22,
        "roof_u_value": 0.18,
        "floor_u_value": 0.25,
        "thermal_mass_level": "medium",
        "thermal_bridge_factor": 0.05,
        "default_infiltration_ach": 0.6,
        **({"company_id": company_id} if company_id else {}),
    }


@tagged("post_install", "-at_install")
class TestLocationBounds(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spec = cls.env["greencube.thermal.specification"].create(_thermal_spec_vals())

    def _create(self, **overrides):
        vals = {"name": "Bounds test", "thermal_specification_id": self.spec.id}
        vals.update(overrides)
        return self.env["greencube.cooling.study"].create(vals)

    def test_latitude_longitude_exactly_zero_is_accepted(self):
        """The equator/Greenwich-meridian case (audit finding: "les tests de
        vérité considèrent parfois latitude/longitude égales à zéro comme
        absentes"). 0.0/0.0 must be a perfectly valid, storable coordinate."""
        study = self._create(latitude=0.0, longitude=0.0, environment_type="coastal")
        self.assertEqual(study.latitude, 0.0)
        self.assertEqual(study.longitude, 0.0)
        # And still correctly flows through get_validation()/
        # _missing_required_sections(): presence is `climate_confirmed`,
        # never `bool(latitude)` (which would be False for 0.0).
        self.assertIn("location", study._missing_required_sections())
        study.climate_confirmed = True
        self.assertNotIn("location", study._missing_required_sections())

    def test_latitude_out_of_bounds_rejected(self):
        with self.assertRaises(ValidationError):
            self._create(latitude=91.0, longitude=0.0)

    def test_latitude_at_bound_accepted(self):
        study = self._create(latitude=90.0, longitude=-180.0)
        self.assertEqual(study.latitude, 90.0)
        self.assertEqual(study.longitude, -180.0)

    def test_longitude_out_of_bounds_rejected(self):
        with self.assertRaises(ValidationError):
            self._create(latitude=0.0, longitude=180.1)

    def test_altitude_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            self._create(latitude=45.0, longitude=5.0, altitude_m=9500.0)

    def test_altitude_within_range_accepted(self):
        study = self._create(latitude=45.0, longitude=5.0, altitude_m=-200.0)
        self.assertEqual(study.altitude_m, -200.0)

    def test_valid_iana_timezone_accepted(self):
        for tz in ("Europe/Paris", "Europe/Zurich"):
            study = self._create(latitude=46.2, longitude=6.1, timezone=tz)
            self.assertEqual(study.timezone, tz)

    def test_invalid_timezone_rejected(self):
        with self.assertRaises(ValidationError):
            self._create(latitude=45.0, longitude=5.0, timezone="Not/AZone")

    def test_utc_offset_only_string_rejected(self):
        """README §13: "Ne jamais retourner uniquement un offset UTC" — a
        bare offset is not a valid IANA zone name either, so it must fail
        the same way any other non-IANA string would."""
        with self.assertRaises(ValidationError):
            self._create(latitude=45.0, longitude=5.0, timezone="UTC+02:00")


@tagged("post_install", "-at_install")
class TestEnvironmentEnumMigration(TransactionCase):
    """Enum alignment + the 18.0.6.0.0 data migration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spec = cls.env["greencube.thermal.specification"].create(_thermal_spec_vals(code="GC-GEO-02"))

    def test_environment_type_selection_uses_dense_urban(self):
        study = self.env["greencube.cooling.study"].create(
            {
                "name": "Enum test",
                "thermal_specification_id": self.spec.id,
                "latitude": 48.85,
                "longitude": 2.35,
                "environment_type": "dense_urban",
            }
        )
        self.assertEqual(study.environment_type, "dense_urban")
        codes = dict(study._fields["environment_type"].selection)
        self.assertIn("dense_urban", codes)
        self.assertNotIn("urban_dense", codes)

    def test_migration_normalizes_legacy_urban_dense_rows(self):
        """Simulates a database that still has the old, invalid
        `urban_dense` value stored (from before both sides were aligned to
        `dense_urban`) and runs the actual 18.0.6.0.0 post-migrate script
        against it."""
        study = self.env["greencube.cooling.study"].create(
            {
                "name": "Legacy enum row",
                "thermal_specification_id": self.spec.id,
                "latitude": 48.85,
                "longitude": 2.35,
            }
        )
        # Written via raw SQL: the ORM would reject 'urban_dense' outright
        # since it is not in the current selection list, exactly the
        # scenario the migration script itself has to work around.
        self.env.cr.execute(
            "UPDATE greencube_cooling_study SET environment_type = 'urban_dense' WHERE id = %s", (study.id,)
        )
        study.invalidate_recordset()
        self.assertEqual(study.environment_type, "urban_dense")

        import importlib.util
        import os

        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "migrations", "18.0.6.0.0", "post-migrate.py"
        )
        spec = importlib.util.spec_from_file_location("gc_geoloc_migration_test", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        module.migrate(self.env.cr, "18.0.5.0.0")
        study.invalidate_recordset()
        self.assertEqual(study.environment_type, "dense_urban")


@tagged("post_install", "-at_install")
class TestGeoCache(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Cache = self.env["greencube.cooling.geo.cache"]

    def test_cache_miss_then_hit(self):
        calls = []

        def fake_get_geo_context(lat, lon):
            calls.append((lat, lon))
            return {"altitude_m": 1200.0, "timezone": "Europe/Zurich", "utc_offset_seconds": 3600}

        with mock.patch.object(geo_service, "get_geo_context", side_effect=fake_get_geo_context):
            first = self.Cache.get_or_fetch_context(46.22, 7.57)
            second = self.Cache.get_or_fetch_context(46.22, 7.57)

        self.assertEqual(first["timezone"], "Europe/Zurich")
        self.assertEqual(second, first)
        # Second call must be a cache hit, not a second provider call.
        self.assertEqual(len(calls), 1)
        entry = self.Cache.search([("cache_key", "like", "context:46.22%")])
        self.assertEqual(entry.status, "available")

    def test_cache_serves_stale_entry_on_provider_failure(self):
        with mock.patch.object(
            geo_service,
            "get_geo_context",
            return_value={"altitude_m": 400.0, "timezone": "Europe/Paris", "utc_offset_seconds": 3600},
        ):
            self.Cache.get_or_fetch_context(48.85, 2.35)

        entry = self.Cache.search([("cache_key", "like", "context:48.85%")])
        # Force it to look expired without waiting for the real TTL.
        entry.fetched_epoch = time.time() - 999999999

        with mock.patch.object(geo_service, "get_geo_context", side_effect=geo_service.GeoServiceError("down")):
            result = self.Cache.get_or_fetch_context(48.85, 2.35)

        self.assertEqual(result["timezone"], "Europe/Paris")
        entry.invalidate_recordset()
        self.assertEqual(entry.status, "stale")

    def test_cache_raises_when_no_fallback_available(self):
        """No cache entry at all + provider down: must fail loudly, never
        invent a coordinate/altitude/timezone (README §5.4/§20)."""
        with mock.patch.object(geo_service, "get_geo_context", side_effect=geo_service.GeoServiceError("down")):
            with self.assertRaises(geo_service.GeoServiceError):
                self.Cache.get_or_fetch_context(10.0, 10.0)

    def test_cache_ttl_is_configurable(self):
        self.env["ir.config_parameter"].sudo().set_param("greencube_cooling.geocoding_cache_ttl_days", "0")
        with mock.patch.object(
            geo_service,
            "get_geo_context",
            return_value={"altitude_m": 10.0, "timezone": "Europe/Lisbon", "utc_offset_seconds": 0},
        ) as fake:
            self.Cache.get_or_fetch_context(38.7, -9.1)
            # TTL of 0 days means the entry is immediately considered
            # expired, so a second call must hit the provider again.
            self.Cache.get_or_fetch_context(38.7, -9.1)
        self.assertEqual(fake.call_count, 2)


@tagged("post_install", "-at_install")
class TestConfirmGeolocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spec = cls.env["greencube.thermal.specification"].create(_thermal_spec_vals(code="GC-GEO-03"))

    def _create(self):
        return self.env["greencube.cooling.study"].create(
            {"name": "Confirm test", "thermal_specification_id": self.spec.id}
        )

    def test_confirm_sets_provenance_precision_and_timestamp(self):
        study = self._create()
        study.action_confirm_geolocation(
            {
                "latitude": 46.2263,
                "longitude": 7.1231,
                "altitude_m": 1200.0,
                "timezone": "Europe/Zurich",
                "environment_type": "mountain",
                "provenance": "geocoded",
                "provider": "open-meteo",
                "precision": "locality",
                "source": {"display_name": "Mission, Anniviers, Suisse", "confidence_percent": 89, "raw_dump": "ignored"},
            }
        )
        self.assertTrue(study.climate_confirmed)
        self.assertEqual(study.location_provenance, "geocoded")
        self.assertEqual(study.location_precision, "locality")
        self.assertEqual(study.location_provider, "open-meteo")
        self.assertTrue(study.location_resolved_at)
        self.assertIn("Mission", study.location_source_json)
        # The extraneous "raw_dump" key must never be persisted.
        self.assertNotIn("raw_dump", study.location_source_json)

    def test_manual_correction_preserves_manual_provenance(self):
        """User first confirms a geocoded result, then manually nudges the
        pin/coordinates and re-confirms as 'manual' — the new provenance
        must overwrite the old one (it is not a blend, it is "how did the
        value that is stored right now get there")."""
        study = self._create()
        study.action_confirm_geolocation(
            {
                "latitude": 46.2263, "longitude": 7.1231, "provenance": "geocoded", "provider": "open-meteo",
                "precision": "locality",
            }
        )
        self.assertEqual(study.location_provenance, "geocoded")

        study.action_confirm_geolocation(
            {"latitude": 46.23, "longitude": 7.12, "provenance": "manual", "precision": "exact"}
        )
        self.assertEqual(study.latitude, 46.23)
        self.assertEqual(study.location_provenance, "manual")
        self.assertEqual(study.location_precision, "exact")
        self.assertFalse(study.location_provider)

    def test_confirm_rejects_unknown_provenance_falls_back_to_manual(self):
        study = self._create()
        study.action_confirm_geolocation({"latitude": 1.0, "longitude": 1.0, "provenance": "not-a-real-source"})
        self.assertEqual(study.location_provenance, "manual")

    def test_confirm_invalidates_frozen_snapshot(self):
        study = self._create()
        study.action_confirm_geolocation({"latitude": 45.0, "longitude": 5.0, "provenance": "manual"})
        snapshot = self.env["greencube.cooling.calculation.snapshot"].create(
            {
                "study_id": study.id,
                "study_revision_number": study.revision_number,
                "thermal_specification_id": self.spec.id,
                "thermal_specification_version": self.spec.version,
                "scenario_codes_json": "[]",
                "payload_json": "{}",
                "snapshot_hash": "gc-geo-test-hash",
                "state": "frozen",
            }
        )
        study.action_confirm_geolocation({"latitude": 45.1, "longitude": 5.1, "provenance": "manual"})
        snapshot.invalidate_recordset()
        self.assertEqual(snapshot.state, "superseded")

    def test_confirm_on_validated_study_requires_revision(self):
        study = self._create()
        study.action_confirm_geolocation({"latitude": 45.0, "longitude": 5.0, "provenance": "manual"})
        study.write({"state": "validated"})
        with self.assertRaises(UserError):
            study.action_confirm_geolocation({"latitude": 46.0, "longitude": 6.0, "provenance": "manual"})

    def test_confirm_rejects_out_of_range_coordinates(self):
        study = self._create()
        with self.assertRaises(ValidationError):
            study.action_confirm_geolocation({"latitude": 200.0, "longitude": 5.0, "provenance": "manual"})
