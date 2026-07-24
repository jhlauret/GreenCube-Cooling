# -*- coding: utf-8 -*-
"""GC-COOLING-02 hardening tests: CORS/Origin enforcement, rate limiting,
idempotency conflict (same key/different inputs), out-of-range field
validation, and the explicit company_id-override rejection.

IMPORTANT — same execution caveat as test_http_api.py: written against
Odoo 18's documented HttpCase API but not executable in an environment
without a live Odoo+Postgres instance. Run with:
odoo-bin -i greencube_cooling --test-tags /greencube_cooling:TestCoolingApiSecurity
--test-enable --stop-after-init -d <test_db>
"""
from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestCoolingApiSecurity(HttpCase):
    BASE = "/api/v1/greencube/cooling"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref("greencube_cooling.group_greencube_cooling_user")
        group_internal_user = cls.env.ref("base.group_user")
        cls.company = cls.env["res.company"].create({"name": "API Security Test Co"})
        cls.user = cls.env["res.users"].create(
            {
                "name": "API Security Test User",
                "login": "api_sec_user@example.com",
                "email": "api_sec_user@example.com",
                "password": "api-sec-test-pwd",
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
                "groups_id": [(6, 0, [group_internal_user.id, group_user.id])],
            }
        )

    def _post(self, path, payload, headers=None):
        return self.opener.request(
            "POST", self.base_url() + self.BASE + path, json=payload, headers=headers or {}, timeout=20
        )

    def _patch(self, path, payload, headers=None):
        return self.opener.request(
            "PATCH", self.base_url() + self.BASE + path, json=payload, headers=headers or {}, timeout=20
        )

    def _put(self, path, payload, headers=None):
        return self.opener.request(
            "PUT", self.base_url() + self.BASE + path, json=payload, headers=headers or {}, timeout=20
        )

    def _get(self, path, headers=None):
        return self.opener.request("GET", self.base_url() + self.BASE + path, headers=headers or {}, timeout=20)

    # ------------------------------------------------------------------
    # CORS / Origin
    # ------------------------------------------------------------------

    def test_mutating_request_from_disallowed_origin_is_rejected(self):
        self.authenticate(self.user.login, "api-sec-test-pwd")
        created = self._post("/studies", {"name": "Origin-guarded study"})
        self.assertEqual(created.status_code, 201, created.text)
        study_id = created.json()["data"]["id"]

        forbidden = self._patch(
            f"/studies/{study_id}",
            {"name": "Should be rejected"},
            headers={"Origin": "https://evil.example.com"},
        )
        self.assertEqual(forbidden.status_code, 403, forbidden.text)
        self.assertEqual(forbidden.json()["error"]["code"], "ACCESS_DENIED")

    def test_mutating_request_from_whitelisted_origin_is_allowed(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.allowed_frontend_origins", "https://app.greencube.example.com"
        )
        self.authenticate(self.user.login, "api-sec-test-pwd")
        created = self._post(
            "/studies",
            {"name": "Whitelisted-origin study"},
            headers={"Origin": "https://app.greencube.example.com"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(
            created.headers.get("Access-Control-Allow-Origin"), "https://app.greencube.example.com"
        )
        self.assertEqual(created.headers.get("Access-Control-Allow-Credentials"), "true")

    def test_cors_preflight_options_answers_without_auth(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.allowed_frontend_origins", "https://app.greencube.example.com"
        )
        preflight = self.opener.request(
            "OPTIONS",
            self.base_url() + self.BASE + "/studies",
            headers={
                "Origin": "https://app.greencube.example.com",
                "Access-Control-Request-Method": "POST",
            },
            timeout=20,
        )
        self.assertEqual(preflight.status_code, 204, preflight.text)
        self.assertEqual(
            preflight.headers.get("Access-Control-Allow-Origin"), "https://app.greencube.example.com"
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_patch_study_out_of_range_field_returns_422_with_fields_detail(self):
        self.authenticate(self.user.login, "api-sec-test-pwd")
        created = self._post("/studies", {"name": "Range-validated study"})
        study_id = created.json()["data"]["id"]

        invalid = self._patch(f"/studies/{study_id}", {"latitude": 200, "target_humidity_percent": 500})
        self.assertEqual(invalid.status_code, 422, invalid.text)
        body = invalid.json()["error"]
        self.assertEqual(body["code"], "VALIDATION_ERROR")
        self.assertIn("latitude", body["fields"])
        self.assertIn("target_humidity_percent", body["fields"])

    def test_patch_study_company_id_override_is_explicitly_rejected(self):
        self.authenticate(self.user.login, "api-sec-test-pwd")
        created = self._post("/studies", {"name": "Company-override study"})
        study_id = created.json()["data"]["id"]

        other_company = self.env["res.company"].create({"name": "Other Co"})
        forbidden = self._patch(f"/studies/{study_id}", {"company_id": other_company.id})
        self.assertEqual(forbidden.status_code, 403, forbidden.text)
        self.assertEqual(forbidden.json()["error"]["code"], "COOLING_COMPANY_OVERRIDE_FORBIDDEN")

    # ------------------------------------------------------------------
    # Idempotency conflict
    # ------------------------------------------------------------------

    def test_idempotency_key_reuse_with_different_inputs_returns_409(self):
        self.authenticate(self.user.login, "api-sec-test-pwd")
        created = self._post("/studies", {"name": "Idempotency conflict study"})
        study_id = created.json()["data"]["id"]
        self._patch(
            f"/studies/{study_id}",
            {"latitude": 43.6, "longitude": 3.9, "environment_type": "suburban", "climate_confirmed": True},
        )
        self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": 6.0, "width_m": 5.0, "height_m": 2.6,
                "wall_u_value": 0.22, "roof_u_value": 0.18, "floor_u_value": 0.25,
                "airtightness_n50": 0.6,
                "facades": [{"orientation": "south", "gross_area_m2": 13.0, "glazing_area_m2": 4.0}],
            },
        )
        self._put(f"/studies/{study_id}/occupancy-profile", {"usage_type": "housing", "usual_occupants": 2})

        first = self._post(
            f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "conflict-key-1"}
        )
        self.assertEqual(first.status_code, 201, first.text)

        # Change a real input (occupant count) that feeds MERCURE, so the
        # snapshot hash differs, then replay the SAME idempotency key.
        self._put(f"/studies/{study_id}/occupancy-profile", {"usage_type": "housing", "usual_occupants": 4})
        second = self._post(
            f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "conflict-key-1"}
        )
        self.assertEqual(second.status_code, 409, second.text)
        self.assertEqual(second.json()["error"]["code"], "IDEMPOTENCY_CONFLICT")

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def test_geocode_rate_limit_returns_429_past_threshold(self):
        self.authenticate(self.user.login, "api-sec-test-pwd")
        response = None
        for _ in range(31):
            response = self.opener.request(
                "GET", self.base_url() + self.BASE + "/geocode?query=Paris", timeout=20
            )
        self.assertEqual(
            response.status_code, 429, "the 31st geocode call in the same minute must be rate-limited"
        )
        self.assertEqual(response.json()["error"]["code"], "RATE_LIMIT_EXCEEDED")
