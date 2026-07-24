# -*- coding: utf-8 -*-
"""HTTP integration tests for controllers/api.py (audit P0-08 / GC-COOLING-02).

IMPORTANT — unexecuted in this environment: there is no Odoo installation
available here (see README.md's verification-limits notes), so these tests
have been written against Odoo 18's documented HttpCase API but have never
actually been run. Do not treat them as passing until they have been
executed against a real Odoo 18 instance (`odoo-bin -i greencube_cooling
--test-tags /greencube_cooling:TestCoolingHttpApi --test-enable
--stop-after-init -d <test_db>` or equivalent). This is the gap the audit
flagged: "Aucun HttpCase ... n'est livré dans le ZIP" — this file exists to
close it, but the claim of coverage is only as good as the first real run.

Covers, through real HTTP requests (not direct ORM calls):
- the full create -> thermal-spec -> occupancy -> ventilation -> validate ->
  calculate -> result wizard flow as a plain "User" group member;
- the job -> result contract (POST /calculations returns a job envelope,
  GET /results/<result_id> returns the full result — not the other way
  around);
- cross-user/cross-company access on a directly-addressed sub-resource
  (equipment load) is rejected with the standard JSON error envelope;
- an unauthenticated request does not return study data;
- optimistic-locking conflict (stale If-Match) on PATCH /studies/<id>.
"""
import json

from odoo.tests.common import HttpCase, tagged


def _thermal_spec_vals(company_id, code):
    return {
        "name": "Studio HTTP test",
        "code": code,
        "version": "1.0",
        "company_id": company_id,
        "length_m": 6.0,
        "width_m": 5.0,
        "height_m": 2.6,
        "wall_u_value": 0.22,
        "roof_u_value": 0.18,
        "floor_u_value": 0.25,
        "thermal_mass_level": "medium",
        "thermal_bridge_factor": 0.05,
        "default_infiltration_ach": 0.6,
    }


@tagged("post_install", "-at_install")
class TestCoolingHttpApi(HttpCase):
    """Runs real HTTP requests (session cookie auth) against
    /api/v1/greencube/cooling, as opposed to TransactionCase tests in
    test_cooling_study.py which call the ORM directly and never exercise
    the controller layer, request/response envelopes, or ir.rule
    enforcement as seen from an actual HTTP client."""

    BASE = "/api/v1/greencube/cooling"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # res.users.create() does not implicitly grant base.group_user (the
        # "Internal User" group web signup normally adds) — without it, the
        # created user can't even read ir.sequence to obtain the study
        # reference on create(), regardless of greencube-specific groups.
        group_user = cls.env.ref("greencube_cooling.group_greencube_cooling_user")
        group_internal_user = cls.env.ref("base.group_user")
        cls.company_a = cls.env["res.company"].create({"name": "HTTP Test Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "HTTP Test Company B"})

        cls.user_a = cls.env["res.users"].create(
            {
                "name": "HTTP User A",
                "login": "http_user_a@example.com",
                "email": "http_user_a@example.com",
                "password": "http-test-pwd-a",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "groups_id": [(6, 0, [group_internal_user.id, group_user.id])],
            }
        )
        cls.user_b = cls.env["res.users"].create(
            {
                "name": "HTTP User B",
                "login": "http_user_b@example.com",
                "email": "http_user_b@example.com",
                "password": "http-test-pwd-b",
                "company_id": cls.company_b.id,
                "company_ids": [(6, 0, [cls.company_b.id])],
                "groups_id": [(6, 0, [group_internal_user.id, group_user.id])],
            }
        )

        # No manual solver-version/catalog-template setup needed here:
        # res.company.create()'s override (models/res_company.py) now
        # auto-provisions both for company_a and company_b as soon as
        # they're created above. Manually creating another active MERCURE
        # version here would raise _check_single_active's UserError since
        # one already exists per company.

    def _post(self, path, payload, headers=None):
        return self.opener.request(
            "POST",
            self.base_url() + self.BASE + path,
            json=payload,
            headers=headers or {},
            timeout=20,
        )

    def _get(self, path, headers=None):
        return self.opener.request("GET", self.base_url() + self.BASE + path, headers=headers or {}, timeout=20)

    def _patch(self, path, payload, headers=None):
        return self.opener.request(
            "PATCH", self.base_url() + self.BASE + path, json=payload, headers=headers or {}, timeout=20
        )

    def _put(self, path, payload, headers=None):
        return self.opener.request(
            "PUT", self.base_url() + self.BASE + path, json=payload, headers=headers or {}, timeout=20
        )

    # ------------------------------------------------------------------

    def test_unauthenticated_request_does_not_return_study_data(self):
        # No self.authenticate() call: the opener carries no session cookie.
        # allow_redirects=False: auth="user" routes 303-redirect anonymous
        # HTTP requests to Odoo's HTML login page, which itself returns 200
        # — following the redirect would make this assertion pass even when
        # the API correctly refused the request, by checking the login
        # page's status instead of the API response's own status.
        response = self.opener.request(
            "GET", self.base_url() + self.BASE + "/studies", allow_redirects=False, timeout=20
        )
        self.assertNotEqual(response.status_code, 200)

    def test_full_wizard_flow_as_standard_user(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")

        created = self._post("/studies", {"name": "HTTP wizard study"})
        self.assertEqual(created.status_code, 201, created.text)
        study_id = created.json()["data"]["id"]

        patched = self._patch(
            f"/studies/{study_id}",
            {
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
                "main_orientation": "south",
            },
        )
        self.assertEqual(patched.status_code, 200, patched.text)

        spec_put = self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": 6.0,
                "width_m": 5.0,
                "height_m": 2.6,
                "wall_u_value": 0.22,
                "roof_u_value": 0.18,
                "floor_u_value": 0.25,
                "airtightness_n50": 0.6,
                "facades": [
                    {"orientation": "south", "gross_area_m2": 13.0, "glazing_area_m2": 4.0, "window_u_value": 1.3},
                ],
            },
        )
        self.assertEqual(spec_put.status_code, 200, spec_put.text)

        occ_put = self._put(
            f"/studies/{study_id}/occupancy-profile",
            {"usage_type": "housing", "usual_occupants": 2, "maximum_occupants": 3},
        )
        self.assertEqual(occ_put.status_code, 200, occ_put.text)

        vent_put = self._put(
            f"/studies/{study_id}/ventilation-profile",
            {"ventilation_type": "simple_flow", "airflow_m3h": 60, "infiltration_ach": 0.6},
        )
        self.assertEqual(vent_put.status_code, 200, vent_put.text)

        validation = self._get(f"/studies/{study_id}/validation")
        self.assertEqual(validation.status_code, 200, validation.text)
        validation_data = validation.json()["data"]
        self.assertTrue(validation_data["ready"], validation_data)
        # Completeness must be computable before any calculation has run
        # (audit P1-05) — this is the whole point of GC-COOLING-13's fix.
        self.assertGreater(validation_data["completeness_score"], 0.0)
        self.assertEqual(validation_data["confidence_score"], 0.0)

        job = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "http-test-key-1"})
        self.assertEqual(job.status_code, 201, job.text)
        job_data = job.json()["data"]
        # The job -> result contract (audit P0-02): the calculation
        # response must NOT already be the full result.
        self.assertIn("job_id", job_data)
        self.assertIn("result_id", job_data)
        self.assertNotIn("recommended_capacity_w", job_data)

        result = self._get(f"/results/{job_data['result_id']}")
        self.assertEqual(result.status_code, 200, result.text)
        result_data = result.json()["data"]
        self.assertGreater(result_data["recommended_capacity_w"], 0)
        self.assertIn("breakdown", result_data)

        # Re-posting with the same Idempotency-Key must not create a second
        # result (audit P1-06).
        job_again = self._post(
            f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "http-test-key-1"}
        )
        self.assertEqual(job_again.status_code, 201, job_again.text)
        self.assertEqual(job_again.json()["data"]["result_id"], job_data["result_id"])

    def test_climate_scenarios_exposed_with_honest_dataset_type(self):
        """GC-COOLING-04: after a calculation, GET /studies/{id} must expose
        location.climate_scenarios[] with provenance/dataset_type, and that
        dataset_type must never be 'projection' — this service only ever
        produces historical data (real API fetch) or an explicit fallback
        heuristic (dataset_type=None), regardless of whether the sandbox
        running this test has outbound network access to Open-Meteo."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")

        created = self._post("/studies", {"name": "HTTP climate study"})
        self.assertEqual(created.status_code, 201, created.text)
        study_id = created.json()["data"]["id"]

        self._patch(
            f"/studies/{study_id}",
            {"latitude": 43.6, "longitude": 3.9, "environment_type": "suburban", "climate_confirmed": True},
        )
        self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": 6.0,
                "width_m": 5.0,
                "height_m": 2.6,
                "wall_u_value": 0.22,
                "roof_u_value": 0.18,
                "floor_u_value": 0.25,
                "airtightness_n50": 0.6,
                "facades": [
                    {"orientation": "south", "gross_area_m2": 13.0, "glazing_area_m2": 4.0, "window_u_value": 1.3},
                ],
            },
        )
        self._put(
            f"/studies/{study_id}/occupancy-profile",
            {"usage_type": "housing", "usual_occupants": 2, "maximum_occupants": 3},
        )
        self._put(
            f"/studies/{study_id}/ventilation-profile",
            {"ventilation_type": "simple_flow", "airflow_m3h": 60, "infiltration_ach": 0.6},
        )

        job = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "http-climate-key-1"})
        self.assertEqual(job.status_code, 201, job.text)

        detail = self._get(f"/studies/{study_id}")
        self.assertEqual(detail.status_code, 200, detail.text)
        scenarios = detail.json()["data"]["location"]["climate_scenarios"]
        self.assertEqual(
            {s["scenario_type"] for s in scenarios},
            {"reference_summer", "hot_weather", "prolonged_heatwave"},
        )
        for s in scenarios:
            self.assertIn(s["provenance"], ("api", "estimated_reference"))
            self.assertNotEqual(s["dataset_type"], "projection")
            if s["provenance"] == "api":
                self.assertEqual(s["dataset_type"], "historical_observed")
                self.assertTrue(s["checksum"])
            else:
                self.assertIsNone(s["dataset_type"])

    def test_cross_user_equipment_load_access_denied(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "User A's study"})
        study_id = created.json()["data"]["id"]
        line = self._post(
            f"/studies/{study_id}/equipment-loads",
            {"name": "Réfrigérateur", "category": "appliance", "quantity": 1, "unit_power_w": 120},
        )
        self.assertEqual(line.status_code, 201, line.text)
        line_id = line.json()["data"]["id"]

        # Switch session to a different user in a different company.
        self.authenticate(self.user_b.login, "http-test-pwd-b")
        forbidden = self._patch(f"/equipment-loads/{line_id}", {"quantity": 5})
        self.assertEqual(forbidden.status_code, 403, forbidden.text)
        self.assertEqual(forbidden.json()["error"]["code"], "COOLING_ACCESS_DENIED")

        forbidden_delete = self.opener.request(
            "DELETE", self.base_url() + self.BASE + f"/equipment-loads/{line_id}", timeout=20
        )
        self.assertEqual(forbidden_delete.status_code, 403, forbidden_delete.text)

    def test_patch_study_stale_if_match_returns_conflict(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Conflict test study"})
        study_id = created.json()["data"]["id"]

        # First PATCH succeeds and changes write_date.
        first = self._patch(f"/studies/{study_id}", {"name": "Renamed once"})
        self.assertEqual(first.status_code, 200, first.text)

        # Second PATCH claims an obsolete write_date via If-Match.
        stale = self._patch(
            f"/studies/{study_id}",
            {"name": "Renamed twice"},
            headers={"If-Match": "2000-01-01T00:00:00"},
        )
        self.assertEqual(stale.status_code, 409, stale.text)
        self.assertEqual(stale.json()["error"]["code"], "COOLING_STUDY_VERSION_CONFLICT")

    def test_two_companies_full_isolation_on_direct_ids(self):
        """Broader companion to test_cross_user_equipment_load_access_denied:
        checks the two other most sensitive directly-addressed resources
        (the study itself, and a calculation result) instead of only
        equipment-loads, plus that the list endpoint never leaks another
        company's study (audit 'deux sociétés/deux utilisateurs' — P2 lot
        qualité item 3)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Company A private study"})
        study_id = created.json()["data"]["id"]
        self._patch(
            f"/studies/{study_id}",
            {"latitude": 43.6, "longitude": 3.9, "environment_type": "suburban", "climate_confirmed": True},
        )
        self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": 6.0,
                "width_m": 5.0,
                "height_m": 2.6,
                "wall_u_value": 0.22,
                "roof_u_value": 0.18,
                "floor_u_value": 0.25,
                "airtightness_n50": 0.6,
                "facades": [{"orientation": "south", "gross_area_m2": 13.0, "glazing_area_m2": 4.0}],
            },
        )
        self._put(f"/studies/{study_id}/occupancy-profile", {"usage_type": "housing", "usual_occupants": 2})
        job = self._post(f"/studies/{study_id}/calculations", {})
        result_id = job.json()["data"]["result_id"]

        self.authenticate(self.user_b.login, "http-test-pwd-b")

        # Company A's study never appears in company B's list.
        listing = self._get("/studies")
        self.assertEqual(listing.status_code, 200, listing.text)
        self.assertNotIn(study_id, [s["id"] for s in listing.json()["data"]])

        # Direct GET on the study itself is denied.
        forbidden_study = self._get(f"/studies/{study_id}")
        self.assertEqual(forbidden_study.status_code, 403, forbidden_study.text)
        self.assertEqual(forbidden_study.json()["error"]["code"], "COOLING_ACCESS_DENIED")

        # Direct GET on the result produced by that study is denied too.
        forbidden_result = self._get(f"/results/{result_id}")
        self.assertEqual(forbidden_result.status_code, 403, forbidden_result.text)
        self.assertEqual(forbidden_result.json()["error"]["code"], "COOLING_ACCESS_DENIED")

    def test_idempotency_key_survives_repeated_retries(self):
        """Simulates a flaky client retrying the same calculation request
        several times in a row (e.g. a dropped response, a user
        double-clicking) — every retry must resolve to the exact same job
        and result, never a duplicate. This is a same-thread, sequential
        approximation of the concurrency requirement: a real concurrent
        (parallel-thread/multi-process) race test would need a running
        multi-worker Odoo instance, which this environment cannot provide —
        see the module-level docstring's execution caveat."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Idempotency retry study"})
        study_id = created.json()["data"]["id"]
        self._patch(
            f"/studies/{study_id}",
            {"latitude": 43.6, "longitude": 3.9, "environment_type": "suburban", "climate_confirmed": True},
        )
        self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": 6.0,
                "width_m": 5.0,
                "height_m": 2.6,
                "wall_u_value": 0.22,
                "roof_u_value": 0.18,
                "floor_u_value": 0.25,
                "airtightness_n50": 0.6,
                "facades": [{"orientation": "south", "gross_area_m2": 13.0, "glazing_area_m2": 4.0}],
            },
        )
        self._put(f"/studies/{study_id}/occupancy-profile", {"usage_type": "housing", "usual_occupants": 2})

        result_ids = set()
        job_ids = set()
        for _ in range(3):
            response = self._post(
                f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "retry-key-xyz"}
            )
            self.assertEqual(response.status_code, 201, response.text)
            data = response.json()["data"]
            result_ids.add(data["result_id"])
            job_ids.add(data["job_id"])

        self.assertEqual(len(result_ids), 1, "each retry must resolve to the same result, not a duplicate")
        self.assertEqual(len(job_ids), 1, "each retry must resolve to the same job, not a duplicate")

        results_list = self._get(f"/studies/{study_id}/results")
        self.assertEqual(len(results_list.json()["data"]), 1, "no duplicate result rows were created")

    # ------------------------------------------------------------------
    # GC-COOLING-16: job/result contract completeness, is_current, and the
    # calculation-job polling endpoint.
    # ------------------------------------------------------------------

    def _create_ready_study(self, name):
        created = self._post("/studies", {"name": name})
        study_id = created.json()["data"]["id"]
        self._patch(
            f"/studies/{study_id}",
            {"latitude": 43.6, "longitude": 3.9, "environment_type": "suburban", "climate_confirmed": True},
        )
        self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": 6.0,
                "width_m": 5.0,
                "height_m": 2.6,
                "wall_u_value": 0.22,
                "roof_u_value": 0.18,
                "floor_u_value": 0.25,
                "airtightness_n50": 0.6,
                "facades": [{"orientation": "south", "gross_area_m2": 13.0, "glazing_area_m2": 4.0}],
            },
        )
        self._put(f"/studies/{study_id}/occupancy-profile", {"usage_type": "housing", "usual_occupants": 2})
        return study_id

    def test_result_exposes_job_id_engine_and_is_current(self):
        """The frontend must never guess which result is the study's
        current one, nor invent a job id from a result id (GC-COOLING-16
        audit finding). GET /results/<id> has to answer both directly."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Result contract study")

        job = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "contract-key-1"})
        self.assertEqual(job.status_code, 201, job.text)
        job_data = job.json()["data"]
        self.assertIn("energyplus_processing_status", job_data)

        result = self._get(f"/results/{job_data['result_id']}")
        self.assertEqual(result.status_code, 200, result.text)
        result_data = result.json()["data"]
        self.assertEqual(result_data["job_id"], job_data["job_id"])
        self.assertEqual(result_data["requested_engine"], "quick_solver")
        self.assertEqual(result_data["energyplus_processing_status"], "not_requested")
        self.assertTrue(result_data["is_current"])

        # The job itself is independently pollable by job_id, and reports
        # the same result_id back (GC-COOLING-16 travaux obligatoires #5:
        # never assume the job response IS the result).
        job_status = self._get(f"/calculations/{job_data['job_id']}")
        self.assertEqual(job_status.status_code, 200, job_status.text)
        job_status_data = job_status.json()["data"]
        self.assertEqual(job_status_data["status"], "completed")
        self.assertEqual(job_status_data["result_id"], job_data["result_id"])

    def test_recalculation_marks_previous_result_not_current(self):
        """Two distinct (non-idempotent-replay) calculations on the same
        study: the first result must stop being reported as `is_current`
        once a second one exists, so a stale browser tab showing the first
        result can detect and flag it (audit: 'ne jamais présenter un
        résultat provisoire/obsolète comme officiel')."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Recalculation study")

        first = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "recalc-key-a"})
        first_result_id = first.json()["data"]["result_id"]

        second = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "recalc-key-b"})
        second_result_id = second.json()["data"]["result_id"]
        self.assertNotEqual(first_result_id, second_result_id)

        stale = self._get(f"/results/{first_result_id}").json()["data"]
        current = self._get(f"/results/{second_result_id}").json()["data"]
        self.assertFalse(stale["is_current"], stale)
        self.assertTrue(current["is_current"], current)

    # ------------------------------------------------------------------
    # GC-COOLING-03: geolocation confirmation over real HTTP
    # ------------------------------------------------------------------

    def test_confirm_location_sets_provenance_and_locks_it_in(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Confirm-location HTTP study"})
        study_id = created.json()["data"]["id"]

        confirmed = self._post(
            f"/studies/{study_id}/confirm-location",
            {
                "latitude": 46.2263,
                "longitude": 7.1231,
                "altitude_m": 1200.0,
                "timezone": "Europe/Zurich",
                "environment_type": "mountain",
                "provenance": "geocoded",
                "provider": "open-meteo",
                "precision": "locality",
                "source": {"display_name": "Mission, Anniviers, Suisse", "confidence_percent": 89},
            },
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.text)
        location = confirmed.json()["data"]["location"]
        self.assertTrue(location["climate_confirmed"])
        self.assertEqual(location["location_provenance"], "geocoded")
        self.assertEqual(location["location_precision"], "locality")
        self.assertEqual(location["location_provider"], "open-meteo")
        self.assertIsNotNone(location["location_resolved_at"])

    def test_confirm_location_rejects_invalid_timezone(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Bad timezone study"})
        study_id = created.json()["data"]["id"]

        response = self._post(
            f"/studies/{study_id}/confirm-location",
            {"latitude": 45.0, "longitude": 5.0, "timezone": "Not/AZone", "provenance": "manual"},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["error"]["code"], "GEO_INVALID_TIMEZONE")

    def test_confirm_location_rejects_out_of_range_coordinates(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Bad coords study"})
        study_id = created.json()["data"]["id"]

        response = self._post(
            f"/studies/{study_id}/confirm-location",
            {"latitude": 200.0, "longitude": 5.0, "provenance": "manual"},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    def test_cross_user_confirm_location_denied(self):
        """A user must never be able to confirm/read the location of a
        study belonging to another user/company by guessing its id
        (GC-COOLING-03 acceptance criterion: API test preventing access to
        another user's study location)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "User A's private study"})
        study_id = created.json()["data"]["id"]

        self.authenticate(self.user_b.login, "http-test-pwd-b")
        forbidden = self._post(
            f"/studies/{study_id}/confirm-location",
            {"latitude": 10.0, "longitude": 10.0, "provenance": "manual"},
        )
        self.assertEqual(forbidden.status_code, 403, forbidden.text)
        self.assertEqual(forbidden.json()["error"]["code"], "COOLING_ACCESS_DENIED")

        forbidden_read = self._get(f"/studies/{study_id}")
        self.assertEqual(forbidden_read.status_code, 403, forbidden_read.text)

    # ------------------------------------------------------------------
    # GC-COOLING-08: thermal specification catalog (Studio/Bureau/Habitat/
    # Commerce), version tracking, and envelope validation.
    # ------------------------------------------------------------------

    def test_catalog_lists_active_versioned_templates_with_distinct_values(self):
        """GET /thermal-specification-templates is what ModelStep fetches
        instead of hardcoding Studio/Bureau/Habitat/Commerce dimensions
        (GC-COOLING-08). Each catalog code must carry its own version and
        genuinely distinct envelope values, not four cards pointing at the
        same numbers."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        response = self._get("/thermal-specification-templates")
        self.assertEqual(response.status_code, 200, response.text)
        templates = response.json()["data"]

        by_code = {t["code"]: t for t in templates}
        for expected_code in ("gc-studio", "gc-office", "gc-living", "gc-commerce"):
            self.assertIn(expected_code, by_code, templates)
            self.assertTrue(by_code[expected_code]["standard_model"])
            self.assertIn("version", by_code[expected_code])

        # Distinct geometry and envelope performance per model — the whole
        # point of a catalog instead of one hardcoded shoebox (audit: "les
        # choix Studio/Bureau/Habitat/Commerce doivent produire des valeurs
        # distinctes").
        dimension_tuples = {
            (t["length_m"], t["width_m"], t["height_m"]) for t in by_code.values()
        }
        wall_u_values = {t["wall_u_value"] for t in by_code.values()}
        self.assertEqual(len(dimension_tuples), 4, "each catalog model must have distinct dimensions")
        self.assertEqual(len(wall_u_values), 4, "each catalog model must have distinct wall U-values")

        # roof_u_value/floor_u_value must be their own values, not a fixed
        # ratio of wall_u_value (GC-COOLING-08 core fix).
        studio = by_code["gc-studio"]
        self.assertEqual(studio["wall_u_value"], 0.18)
        self.assertEqual(studio["roof_u_value"], 0.16)
        self.assertEqual(studio["floor_u_value"], 0.20)
        self.assertNotAlmostEqual(studio["roof_u_value"], studio["wall_u_value"] * 0.9)

    def test_applying_catalog_template_freezes_resolved_values_into_snapshot(self):
        """Selecting "GreenCube Bureau" must resolve every envelope value
        (wall/roof/floor U, dimensions) from that specific template version
        into the study's own specification, and action_create_snapshot()
        must freeze those resolved numbers — never a bare template
        reference that could later drift (GC-COOLING-08 pt.9)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        catalog = self._get("/thermal-specification-templates").json()["data"]
        office = next(t for t in catalog if t["code"] == "gc-office")

        study_id = self._create_ready_study("Bureau snapshot study")
        spec_put = self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": office["length_m"],
                "width_m": office["width_m"],
                "height_m": office["height_m"],
                "wall_u_value": office["wall_u_value"],
                "roof_u_value": office["roof_u_value"],
                "floor_u_value": office["floor_u_value"],
                "airtightness_n50": office["airtightness_n50"],
                "source_template_id": office["id"],
                "facades": [{"orientation": "south", "gross_area_m2": 8.1, "glazing_area_m2": 5.0}],
            },
        )
        self.assertEqual(spec_put.status_code, 200, spec_put.text)
        spec_data = spec_put.json()["data"]
        self.assertEqual(spec_data["source_template_id"], office["id"])
        self.assertEqual(spec_data["source_template_version"], office["version"])
        self.assertEqual(spec_data["roof_u_value"], office["roof_u_value"])
        self.assertEqual(spec_data["floor_u_value"], office["floor_u_value"])

    def test_customization_persists_and_is_not_overwritten_by_reapplying_same_values(self):
        """Once a study's specification has diverged from its source
        template (a user edited the roof U-value), that customization must
        survive — re-fetching the spec must never silently snap back to
        the template's own values (GC-COOLING-08 pt.7: never silently
        overwrite a customization)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        catalog = self._get("/thermal-specification-templates").json()["data"]
        studio = next(t for t in catalog if t["code"] == "gc-studio")

        study_id = self._create_ready_study("Customization study")
        self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": studio["length_m"],
                "width_m": studio["width_m"],
                "height_m": studio["height_m"],
                "wall_u_value": studio["wall_u_value"],
                "roof_u_value": studio["roof_u_value"],
                "floor_u_value": studio["floor_u_value"],
                "airtightness_n50": studio["airtightness_n50"],
                "source_template_id": studio["id"],
            },
        )
        # Customize the roof U-value only.
        customized = self._put(
            f"/studies/{study_id}/thermal-specification",
            {"roof_u_value": 0.45},
        )
        self.assertEqual(customized.status_code, 200, customized.text)
        self.assertEqual(customized.json()["data"]["roof_u_value"], 0.45)

        # Simulate the page reloading and re-fetching: the customization
        # must still be there, not reset to the template's 0.16.
        reloaded = self._get(f"/studies/{study_id}/thermal-specification")
        self.assertEqual(reloaded.status_code, 200, reloaded.text)
        self.assertEqual(reloaded.json()["data"]["roof_u_value"], 0.45)
        self.assertEqual(reloaded.json()["data"]["source_template_id"], studio["id"])

    def test_new_template_version_does_not_retroactively_mutate_older_studies(self):
        """Bumping a catalog template to a new version (action_create_new_
        version) must never change the values of a study that already
        forked from the old version (GC-COOLING-08 pt.8: a version change
        must not retroactively mutate old studies)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        catalog = self._get("/thermal-specification-templates").json()["data"]
        living = next(t for t in catalog if t["code"] == "gc-living")

        study_id = self._create_ready_study("Old-version study")
        self._put(
            f"/studies/{study_id}/thermal-specification",
            {
                "length_m": living["length_m"],
                "width_m": living["width_m"],
                "height_m": living["height_m"],
                "wall_u_value": living["wall_u_value"],
                "roof_u_value": living["roof_u_value"],
                "floor_u_value": living["floor_u_value"],
                "airtightness_n50": living["airtightness_n50"],
                "source_template_id": living["id"],
            },
        )
        before = self._get(f"/studies/{study_id}/thermal-specification").json()["data"]

        # Bump the catalog template itself to a new version via the ORM
        # (mirrors action_create_new_version(), which a manager would
        # trigger from the backend UI).
        template = self.env["greencube.thermal.specification"].browse(living["id"])
        template.sudo().action_create_new_version()

        after = self._get(f"/studies/{study_id}/thermal-specification").json()["data"]
        self.assertEqual(after["roof_u_value"], before["roof_u_value"])
        self.assertEqual(after["floor_u_value"], before["floor_u_value"])
        self.assertEqual(after["source_template_version"], living["version"])

    def test_thermal_specification_rejects_out_of_range_u_value(self):
        """A wall/roof/floor U-value outside the physically plausible
        0.05-6.00 W/m².K band must be rejected with a structured 422, not
        silently accepted (GC-COOLING-08 mandatory test: out-of-range
        U-value rejected)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Bad U-value study")

        response = self._put(
            f"/studies/{study_id}/thermal-specification",
            {"wall_u_value": 999.0},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response.json()["error"]["field"], "wall_u_value")

    def test_thermal_specification_rejects_negative_facade_surface(self):
        """A negative facade surface must never reach the database (GC-
        COOLING-08 mandatory test: negative surface rejected)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Negative surface study")

        response = self._put(
            f"/studies/{study_id}/thermal-specification",
            {"facades": [{"orientation": "south", "gross_area_m2": -5.0, "glazing_area_m2": 0}]},
        )
        self.assertEqual(response.status_code, 422, response.text)

    def test_thermal_specification_rejects_inconsistent_glazing(self):
        """Glazing area greater than the facade's own gross area is
        physically inconsistent and must be rejected (GC-COOLING-08
        mandatory test: inconsistent glazing rejected)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Inconsistent glazing study")

        response = self._put(
            f"/studies/{study_id}/thermal-specification",
            {"facades": [{"orientation": "south", "gross_area_m2": 5.0, "glazing_area_m2": 20.0}]},
        )
        self.assertEqual(response.status_code, 422, response.text)

    # ------------------------------------------------------------------
    # Solar shading (GC-COOLING-09)
    # ------------------------------------------------------------------

    def test_shading_put_persists_distinct_entries_per_orientation(self):
        """Each protection type/orientation pair must be stored and
        returned as its own record — never collapsed onto a single
        generic type (GC-COOLING-09 audit finding: 'tous les types de
        protection sont réduits à external_blind')."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Shading study")

        response = self._put(
            f"/studies/{study_id}/shading",
            [
                {"orientation": "south", "shading_type": "overhang", "efficiency_percent": 35, "confirmed": True},
                {"orientation": "west", "shading_type": "external_blind", "efficiency_percent": 50, "confirmed": True},
            ],
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(len(data), 2)
        by_orientation = {e["orientation"]: e for e in data}
        self.assertEqual(by_orientation["south"]["shading_type"], "overhang")
        self.assertEqual(by_orientation["west"]["shading_type"], "external_blind")
        self.assertNotEqual(by_orientation["south"]["shading_type"], by_orientation["west"]["shading_type"])

        get_response = self._get(f"/studies/{study_id}/shading")
        self.assertEqual(get_response.status_code, 200, get_response.text)
        self.assertEqual(len(get_response.json()["data"]), 2)

    def test_shading_put_with_fewer_entries_removes_the_dropped_orientation(self):
        """Removing a protection in the UI must actually delete/neutralize
        it backend-side, not leave a stale record active (GC-COOLING-09
        pt.8: 'supprimer côté backend une protection retirée dans l'UI')."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Shading removal study")

        self._put(
            f"/studies/{study_id}/shading",
            [
                {"orientation": "south", "shading_type": "overhang", "efficiency_percent": 35, "confirmed": True},
                {"orientation": "west", "shading_type": "external_blind", "efficiency_percent": 50, "confirmed": True},
            ],
        )

        response = self._put(
            f"/studies/{study_id}/shading",
            [{"orientation": "south", "shading_type": "overhang", "efficiency_percent": 35, "confirmed": True}],
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["orientation"], "south")

        response_empty = self._put(f"/studies/{study_id}/shading", [])
        self.assertEqual(response_empty.status_code, 200, response_empty.text)
        self.assertEqual(response_empty.json()["data"], [])
        self.assertEqual(self._get(f"/studies/{study_id}/shading").json()["data"], [])

    def test_shading_rejects_out_of_range_efficiency(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Shading invalid efficiency study")

        response = self._put(
            f"/studies/{study_id}/shading",
            [{"orientation": "south", "shading_type": "overhang", "efficiency_percent": 150}],
        )
        self.assertEqual(response.status_code, 422, response.text)

    def test_result_exposes_solar_gain_by_facade(self):
        """The result contract must surface which orientation drives the
        solar load (GC-COOLING-09 pt.11), decomposing but never inflating
        the aggregate 'solar_glazing' breakdown total."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Solar gain by facade study")

        job = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "solar-gain-key-1"})
        self.assertEqual(job.status_code, 201, job.text)
        result = self._get(f"/results/{job.json()['data']['result_id']}")
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()["data"]

        self.assertIn("solar_gain_by_facade", data)
        self.assertEqual(len(data["solar_gain_by_facade"]), 1)
        entry = data["solar_gain_by_facade"][0]
        self.assertEqual(entry["facade"], "south")
        self.assertGreater(entry["gain_w"], 0)
        solar_breakdown = next(c for c in data["breakdown"] if c["component_code"] == "solar_glazing")
        self.assertAlmostEqual(
            sum(e["gain_w"] for e in data["solar_gain_by_facade"]), solar_breakdown["total_w"], places=3
        )

    def test_occupancy_profile_put_and_get_round_trip_weekly_schedule(self):
        """GC-COOLING-10: the weekly calendar (active_<weekday> booleans)
        and the derived schedule fields must round-trip through the real
        HTTP contract, not just the ORM."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Weekly schedule study"})
        study_id = created.json()["data"]["id"]

        put = self._put(
            f"/studies/{study_id}/occupancy-profile",
            {
                "usage_type": "housing",
                "usual_occupants": 2,
                "maximum_occupants": 3,
                "start_hour": 22.0,
                "end_hour": 6.0,
                "active_monday": True,
                "active_tuesday": True,
                "active_wednesday": True,
                "active_thursday": True,
                "active_friday": True,
                "active_saturday": True,
                "active_sunday": True,
            },
        )
        self.assertEqual(put.status_code, 200, put.text)
        data = put.json()["data"]
        self.assertTrue(data["crosses_midnight"])
        self.assertEqual(data["daily_occupied_hours"], 8.0)
        self.assertAlmostEqual(data["occupancy_fraction"], 8.0 / 24.0)
        self.assertEqual(data["active_days_count"], 7)

        get = self._get(f"/studies/{study_id}/occupancy-profile")
        self.assertEqual(get.status_code, 200, get.text)
        self.assertTrue(get.json()["data"]["active_sunday"])

    def test_occupancy_profile_rejects_out_of_range_occupant_count(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Occupant bound study"})
        study_id = created.json()["data"]["id"]

        response = self._put(
            f"/studies/{study_id}/occupancy-profile",
            {"usage_type": "office", "usual_occupants": 5000, "maximum_occupants": 5000},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    def test_occupancy_profile_locked_after_validation_returns_409(self):
        """A validated study's occupancy data must be read-only end to
        end: PUT must answer a structured 409 INVALID_STATE, never a raw
        UserError/500 (GC-COOLING-10 -- this study-level lock previously
        only covered the study's own fields, never its sub-models)."""
        technician_group = self.env.ref("greencube_cooling.group_greencube_cooling_technician")
        self.user_a.write({"groups_id": [(4, technician_group.id)]})
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Validated occupancy lock study")
        self._put(
            f"/studies/{study_id}/ventilation-profile",
            {"ventilation_type": "simple_flow", "airflow_m3h": 60, "infiltration_ach": 0.6},
        )

        job = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "lock-key-1"})
        self.assertEqual(job.status_code, 201, job.text)

        validated = self._post(f"/studies/{study_id}/validate", {})
        self.assertEqual(validated.status_code, 200, validated.text)

        blocked = self._put(f"/studies/{study_id}/occupancy-profile", {"usual_occupants": 9})
        self.assertEqual(blocked.status_code, 409, blocked.text)
        self.assertEqual(blocked.json()["error"]["code"], "INVALID_STATE")

    def test_equipment_load_catalog_comes_from_odoo_not_hardcoded(self):
        """GET /equipment-load-catalog is what EquipmentStep fetches instead
        of hardcoding its list of internal-load templates (GC-COOLING-11).
        Only products flagged `is_internal_load_equipment` are returned, and
        each carries the reference values a study line is initialized from
        — including a real (non-'other') category, since the catalog's
        battery/UPS entries must not be folded into 'other'."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        response = self._get("/equipment-load-catalog")
        self.assertEqual(response.status_code, 200, response.text)
        items = response.json()["data"]

        by_code = {i["code"]: i for i in items}
        for expected_code in ("laptop", "monitor", "printer", "server", "led", "coffee", "network", "battery", "ups"):
            self.assertIn(expected_code, by_code, items)

        laptop = by_code["laptop"]
        self.assertEqual(laptop["category"], "it")
        self.assertEqual(laptop["unit_power_w"], 45)
        self.assertEqual(laptop["usage_hours_per_day"], 8)
        self.assertEqual(laptop["simultaneity_percent"], 100)

        self.assertEqual(by_code["battery"]["category"], "battery")
        self.assertEqual(by_code["ups"]["category"], "inverter")

        # The cooling-equipment-to-install catalog (is_cooling_equipment)
        # must never leak into this internal-loads catalog.
        equipment_catalog = self._get("/equipment-catalog").json()["data"]
        equipment_names = {p["name"] for p in equipment_catalog}
        internal_load_names = {i["name"] for i in items}
        self.assertFalse(equipment_names & internal_load_names)

    def test_equipment_load_create_with_product_id_from_catalog(self):
        """Adding an equipment line from the catalog keeps `product_id` on
        the created line (round-trip needed by the frontend to match a
        reloaded line back to its catalog card by identity, not name)."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        created = self._post("/studies", {"name": "Equipment catalog study"})
        study_id = created.json()["data"]["id"]

        catalog = self._get("/equipment-load-catalog").json()["data"]
        laptop = next(i for i in catalog if i["code"] == "laptop")

        response = self._post(
            f"/studies/{study_id}/equipment-loads",
            {
                "product_id": laptop["id"],
                "name": laptop["name"],
                "category": laptop["category"],
                "quantity": 3,
                "unit_power_w": laptop["unit_power_w"],
                "usage_hours_per_day": laptop["usage_hours_per_day"],
                "simultaneity_percent": laptop["simultaneity_percent"],
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["data"]["product_id"], laptop["id"])

        listed = self._get(f"/studies/{study_id}/equipment-loads")
        self.assertEqual(listed.json()["data"][0]["product_id"], laptop["id"])

    # -- GC-COOLING-18: equipment recommendation / selection / validation --

    def _create_cooling_product(self, **overrides):
        vals = {
            "name": "HTTP test split 3.5kW",
            "is_cooling_equipment": True,
            "cooling_equipment_type": "split_wall",
            "nominal_capacity_w": 3500,
            "capacity_at_35c_w": 3300,
            "capacity_at_45c_w": 3200,
            "electrical_power_w": 950,
            "eer": 3.4,
            "seer": 6.2,
            "cooling_shr": 0.8,
            "noise_db": 40,
            "max_outdoor_temperature_c": 46,
            "power_supply": "monophase",
            "data_quality": "catalog",
            "list_price": 1999.0,
        }
        vals.update(overrides)
        return self.env["product.template"].sudo().create(vals)

    def test_equipment_recommendation_and_selection_flow(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Equipment selection study")
        job = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "equip-key-1"})
        self.assertEqual(job.status_code, 201, job.text)

        product = self._create_cooling_product()

        recommendations = self._post(f"/studies/{study_id}/equipment-recommendations", {})
        self.assertEqual(recommendations.status_code, 200, recommendations.text)
        rows = recommendations.json()["data"]
        self.assertTrue(any(r["product"]["id"] == product.id for r in rows))

        created = self._post(f"/studies/{study_id}/equipment-selections", {"product_id": product.id})
        self.assertEqual(created.status_code, 201, created.text)
        selection = created.json()["data"]
        self.assertEqual(selection["state"], "selected")
        self.assertIsNone(selection["validated_at"])

        validated = self._post(f"/studies/{study_id}/equipment-selections/{selection['id']}/validate", {})
        self.assertEqual(validated.status_code, 200, validated.text)
        validated_data = validated.json()["data"]
        self.assertEqual(validated_data["state"], "validated")
        self.assertIsNotNone(validated_data["validated_at"])

        # Validating a second time is refused, not a silent re-stamp.
        revalidate = self._post(f"/studies/{study_id}/equipment-selections/{selection['id']}/validate", {})
        self.assertEqual(revalidate.status_code, 409, revalidate.text)
        self.assertEqual(revalidate.json()["error"]["code"], "COOLING_SELECTION_ALREADY_EXISTS")

        # A new selection supersedes the validated one without deleting it.
        product_2 = self._create_cooling_product(name="HTTP test split 3.5kW (v2)")
        replacement = self._post(f"/studies/{study_id}/equipment-selections", {"product_id": product_2.id})
        self.assertEqual(replacement.status_code, 201, replacement.text)
        self.assertEqual(replacement.json()["data"]["supersedes_id"], selection["id"])

        history = self._get(f"/studies/{study_id}/equipment-selections").json()["data"]
        states_by_id = {row["id"]: row["state"] for row in history}
        self.assertEqual(states_by_id[selection["id"]], "validated")
        self.assertEqual(states_by_id[replacement.json()["data"]["id"]], "selected")

    def test_equipment_selection_rejects_product_with_insufficient_data(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Equipment insufficient data study")
        self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "equip-key-2"})

        product = self._create_cooling_product(
            name="HTTP test split (no data)", capacity_at_45c_w=0, max_outdoor_temperature_c=0, cooling_shr=0
        )

        recommendations = self._post(f"/studies/{study_id}/equipment-recommendations", {}).json()["data"]
        row = next(r for r in recommendations if r["product"]["id"] == product.id)
        self.assertEqual(row["status"], "insufficient_data")

        selection = self._post(f"/studies/{study_id}/equipment-selections", {"product_id": product.id})
        self.assertEqual(selection.status_code, 422, selection.text)
        self.assertEqual(selection.json()["error"]["code"], "COOLING_PRODUCT_DATA_INCOMPLETE")

    def test_equipment_recommendations_blocked_when_result_is_stale(self):
        """GC-COOLING-18 acceptance criterion: "un résultat obsolète bloque
        la sélection". Once the frozen snapshot a result was computed from
        has been superseded by a later input edit, equipment-recommendations
        must refuse to use that result.

        `_invalidate_active_snapshot()` is called directly here (as the
        API's own section-editing PUT endpoints do internally) rather than
        through a PUT after action_calculate(): PUT /thermal-specification
        on an already-calculated study hits a pre-existing, unrelated bug
        (it tries to create a *new* private spec reusing the same
        study-scoped `code`, which collides with a unique constraint —
        see docs/cooling_equipment_limitations.md) that is out of scope for
        this equipment-selection lot and shouldn't gate this test."""
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Equipment stale result study")
        job = self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "equip-stale-key-1"})
        self.assertEqual(job.status_code, 201, job.text)

        self.env["greencube.cooling.study"].sudo().browse(study_id)._invalidate_active_snapshot()

        recommendations = self._post(f"/studies/{study_id}/equipment-recommendations", {})
        self.assertEqual(recommendations.status_code, 422, recommendations.text)
        self.assertEqual(recommendations.json()["error"]["code"], "COOLING_RESULT_STALE")

    def test_cross_user_cannot_validate_or_read_another_users_equipment_selection(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        study_id = self._create_ready_study("Equipment IDOR study")
        self._post(f"/studies/{study_id}/calculations", {}, headers={"Idempotency-Key": "equip-idor-key-1"})
        product = self._create_cooling_product(name="HTTP test split (IDOR)")
        created = self._post(f"/studies/{study_id}/equipment-selections", {"product_id": product.id})
        selection_id = created.json()["data"]["id"]

        self.authenticate(self.user_b.login, "http-test-pwd-b")
        cross_list = self._get(f"/studies/{study_id}/equipment-selections")
        self.assertEqual(cross_list.status_code, 403, cross_list.text)

        cross_validate = self._post(f"/studies/{study_id}/equipment-selections/{selection_id}/validate", {})
        self.assertIn(cross_validate.status_code, (403, 404), cross_validate.text)

    # ------------------------------------------------------------------
    # GC-COOLING-15: EnergyPlus worker hand-off routes and job cancellation.
    #
    # /energyplus-jobs/claim and /energyplus-jobs/<id>/complete are called
    # by the standalone energyplus_worker/ process, never by a logged-in
    # browser session — so these use self.opener directly (a plain
    # requests.Session) with the shared worker-key header instead of
    # self._post/_get, which assume auth="user" session-cookie routes.
    # ------------------------------------------------------------------

    def _worker_request(self, method, path, payload=None, worker_key="test-worker-key-xyz"):
        headers = {"Content-Type": "application/json"}
        if worker_key is not None:
            headers["X-GreenCube-Worker-Key"] = worker_key
        return self.opener.request(
            method,
            self.base_url() + self.BASE + path,
            data=json.dumps(payload if payload is not None else {}),
            headers=headers,
            timeout=20,
        )

    def _queue_energyplus_job(self, name):
        """Creates a ready study and runs it through action_calculate(engine="both")
        with EnergyPlus force-enabled, landing its job in
        energyplus_processing_status == 'queued_for_worker' — the real
        state the /energyplus-jobs/claim route looks for. Patches the same
        `is_energyplus_enabled` symbol cooling_study.py imports; the HTTP
        request runs synchronously inside the `with` block so this is safe
        even though HttpCase serves it from a background thread."""
        from unittest import mock

        study_id = self._create_ready_study(name)
        with mock.patch(
            "odoo.addons.greencube_cooling.models.cooling_study.is_energyplus_enabled", return_value=True
        ):
            response = self._post(
                f"/studies/{study_id}/calculations",
                {"engine": "both"},
                headers={"Idempotency-Key": f"energyplus-{name}"},
            )
        self.assertEqual(response.status_code, 201, response.text)
        job_id = response.json()["data"]["job_id"]
        self.assertEqual(
            response.json()["data"]["energyplus_processing_status"],
            "queued_for_worker",
            response.text,
        )
        return study_id, job_id

    def test_energyplus_worker_endpoints_disabled_without_configured_key(self):
        # No greencube_cooling.energyplus_worker_key set at all in this test
        # DB: the endpoint must fail closed (503), never accept an
        # unauthenticated claim.
        response = self._worker_request("POST", "/energyplus-jobs/claim", worker_key=None)
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(response.json()["error"]["code"], "ENERGYPLUS_WORKER_NOT_CONFIGURED")

    def test_energyplus_worker_endpoints_reject_wrong_key(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.energyplus_worker_key", "the-real-key"
        )
        response = self._worker_request("POST", "/energyplus-jobs/claim", worker_key="not-the-real-key")
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.json()["error"]["code"], "ENERGYPLUS_WORKER_UNAUTHORIZED")

    def test_energyplus_worker_claim_and_complete_round_trip(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.energyplus_worker_key", "the-real-key"
        )
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        _study_id, job_id = self._queue_energyplus_job("worker round trip")

        claim = self._worker_request("POST", "/energyplus-jobs/claim", worker_key="the-real-key")
        self.assertEqual(claim.status_code, 200, claim.text)
        claimed = claim.json()["data"]
        self.assertEqual(claimed["job_id"], job_id)
        self.assertIn("payload_json", claimed)
        self.assertIn("snapshot_hash", claimed)

        # Nothing else is queued: a second claim call must return 204, not
        # the same job again (no double-dispatch to two workers).
        second_claim = self._worker_request("POST", "/energyplus-jobs/claim", worker_key="the-real-key")
        self.assertEqual(second_claim.status_code, 204, second_claim.text)

        complete = self._worker_request(
            "POST",
            f"/energyplus-jobs/{job_id}/complete",
            payload={
                "status": "simulation_completed",
                "artifacts": [
                    {
                        "artifact_type": "sql",
                        "filename": "eplusout.sql",
                        "checksum_sha256": "a" * 64,
                        "content_b64": "aGVsbG8=",
                    }
                ],
            },
            worker_key="the-real-key",
        )
        self.assertEqual(complete.status_code, 200, complete.text)
        self.assertEqual(complete.json()["data"]["energyplus_processing_status"], "simulation_completed")

        job_after = self._get(f"/calculations/{job_id}")
        self.assertEqual(job_after.json()["data"]["energyplus_processing_status"], "simulation_completed")

    def test_energyplus_worker_complete_rejects_malformed_artifact(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.energyplus_worker_key", "the-real-key"
        )
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        _study_id, job_id = self._queue_energyplus_job("worker malformed artifact")
        self._worker_request("POST", "/energyplus-jobs/claim", worker_key="the-real-key")

        response = self._worker_request(
            "POST",
            f"/energyplus-jobs/{job_id}/complete",
            payload={"status": "simulation_completed", "artifacts": [{"artifact_type": "sql"}]},
            worker_key="the-real-key",
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["error"]["code"], "INVALID_PAYLOAD")

    def test_energyplus_worker_complete_rejects_job_not_claimed(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.energyplus_worker_key", "the-real-key"
        )
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        _study_id, job_id = self._queue_energyplus_job("worker not claimed")
        # Never claimed -> still queued_for_worker, not simulation_running.
        response = self._worker_request(
            "POST",
            f"/energyplus-jobs/{job_id}/complete",
            payload={"status": "simulation_completed"},
            worker_key="the-real-key",
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["error"]["code"], "ENERGYPLUS_JOB_STATE_CONFLICT")

    def test_cancel_calculation_while_queued_succeeds(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        _study_id, job_id = self._queue_energyplus_job("cancel queued")
        response = self._post(f"/calculations/{job_id}/cancel", {})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["energyplus_processing_status"], "cancelled")

    def test_cancel_calculation_after_claim_is_conflict(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.energyplus_worker_key", "the-real-key"
        )
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        _study_id, job_id = self._queue_energyplus_job("cancel after claim")
        self._worker_request("POST", "/energyplus-jobs/claim", worker_key="the-real-key")

        response = self._post(f"/calculations/{job_id}/cancel", {})
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["error"]["code"], "COOLING_JOB_NOT_CANCELLABLE")

    def test_cross_user_cannot_cancel_or_read_another_users_calculation(self):
        self.authenticate(self.user_a.login, "http-test-pwd-a")
        _study_id, job_id = self._queue_energyplus_job("cancel idor")

        self.authenticate(self.user_b.login, "http-test-pwd-b")
        cross_get = self._get(f"/calculations/{job_id}")
        self.assertIn(cross_get.status_code, (403, 404), cross_get.text)
        cross_cancel = self._post(f"/calculations/{job_id}/cancel", {})
        self.assertIn(cross_cancel.status_code, (403, 404), cross_cancel.text)
