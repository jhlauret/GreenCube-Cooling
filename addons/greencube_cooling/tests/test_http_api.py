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

        # greencube.cooling.solver.version is company-scoped (required
        # company_id + a strict company_id-in-company_ids rule, same
        # convention as greencube.thermal.specification) — the demo solver
        # version installed with the module only belongs to the default
        # company, so action_calculate() would otherwise fail for every
        # freshly-created company with SOLVER_VERSION_MISSING regardless of
        # how complete the study itself is.
        cls.env["greencube.cooling.solver.version"].sudo().create(
            {"name": "MERCURE test (A)", "code": "MERCURE", "version": "1.0.0-test", "state": "active", "company_id": cls.company_a.id}
        )
        cls.env["greencube.cooling.solver.version"].sudo().create(
            {"name": "MERCURE test (B)", "code": "MERCURE", "version": "1.0.0-test", "state": "active", "company_id": cls.company_b.id}
        )

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
