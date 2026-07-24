# -*- coding: utf-8 -*-
"""TransactionCase tests for greencube.cooling.calculation.job's
orchestration behaviour (GC-COOLING-15): worker claim/complete, retry with
attempt-count/dead-letter, stall detection, cancellation, and the
write-guard on finished jobs.

These are ORM-level tests (not HTTP) — they exercise the same model
methods the /energyplus-jobs/claim, /energyplus-jobs/<id>/complete and
/calculations/<id>/cancel routes call (controllers/api.py), without going
through the HTTP layer itself (see tests/test_http_api.py for those).
"""
import datetime
from unittest import mock

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


def _thermal_spec_vals():
    return {
        "name": "Studio job-orchestration test",
        "code": "GC-JOB-30",
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
    }


@tagged("post_install", "-at_install")
class TestCalculationJobOrchestration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        technician_group = cls.env.ref("greencube_cooling.group_greencube_cooling_technician")
        cls.env.user.write({"groups_id": [(4, technician_group.id)]})
        cls.spec = cls.env["greencube.thermal.specification"].create(_thermal_spec_vals())
        cls.env["greencube.thermal.facade"].create(
            {
                "thermal_specification_id": cls.spec.id,
                "orientation": "south",
                "gross_area_m2": 10.0,
                "glazing_area_m2": 4.0,
                "window_u_value": 1.3,
                "solar_factor_g": 0.5,
                "default_shading_factor": 0.7,
            }
        )

    def _create_ready_study(self):
        study = self.env["greencube.cooling.study"].create(
            {
                "name": "Étude orchestration job",
                "thermal_specification_id": self.spec.id,
                "latitude": 43.6,
                "longitude": 3.9,
                "environment_type": "suburban",
                "climate_confirmed": True,
            }
        )
        self.env["greencube.cooling.occupancy.profile"].create(
            {"study_id": study.id, "usage_type": "housing", "usual_occupants": 2, "maximum_occupants": 3}
        )
        self.env["greencube.cooling.equipment.load"].create(
            {
                "study_id": study.id,
                "name": "Ordinateur portable",
                "category": "it",
                "quantity": 1,
                "unit_power_w": 45,
                "usage_hours_per_day": 8,
                "simultaneity_percent": 100,
            }
        )
        self.env["greencube.cooling.ventilation.profile"].create(
            {
                "study_id": study.id,
                "ventilation_type": "simple_flow",
                "airflow_m3h": 60,
                "heat_recovery_efficiency_percent": 0,
                "infiltration_ach": 0.6,
            }
        )
        study.action_mark_ready()
        self.assertEqual(study.state, "ready")
        return study

    def _create_queued_energyplus_job(self):
        """Runs action_calculate(engine="both") with EnergyPlus force-enabled
        so the (real, tested) inline Honeybee translation succeeds and the
        job lands in energyplus_processing_status == 'queued_for_worker' —
        exactly the state /energyplus-jobs/claim looks for. This never
        calls run_energyplus_simulation() (still forbidden inline); it only
        exercises the hand-off bookkeeping this test file is about."""
        study = self._create_ready_study()
        with mock.patch("odoo.addons.greencube_cooling.models.cooling_study.is_energyplus_enabled", return_value=True):
            study.action_create_snapshot(engine="both")
            result = study.action_calculate(engine="both")
        job = self.env["greencube.cooling.calculation.job"].search([("result_id", "=", result.id)], limit=1)
        self.assertTrue(job)
        self.assertEqual(job.energyplus_processing_status, "queued_for_worker")
        self.assertEqual(job.attempt_count, 0)
        return job

    # ------------------------------------------------------------------
    # Claim / complete hand-off
    # ------------------------------------------------------------------

    def test_claim_next_for_worker_marks_running_and_increments_attempt(self):
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]

        claimed = Job._claim_next_for_worker()
        self.assertEqual(claimed.id, job.id)
        self.assertEqual(claimed.energyplus_processing_status, "simulation_running")
        self.assertEqual(claimed.attempt_count, 1)
        self.assertTrue(claimed.claimed_at)

    def test_claim_next_for_worker_returns_none_when_nothing_queued(self):
        Job = self.env["greencube.cooling.calculation.job"]
        # No queued_for_worker rows exist yet in this fresh transaction.
        self.assertFalse(Job.search([("energyplus_processing_status", "=", "queued_for_worker")]))
        self.assertFalse(Job._claim_next_for_worker())

    def test_claim_next_for_worker_does_not_return_an_already_claimed_job(self):
        """Once claimed, a job is no longer 'queued_for_worker', so a second
        claim call (simulating a second worker process) must not return it
        again — this is the practical, single-process-testable half of the
        FOR UPDATE SKIP LOCKED concurrency guarantee (true concurrent
        claims from two DB connections need a multi-cursor test, which is
        out of scope for a plain TransactionCase)."""
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]
        first = Job._claim_next_for_worker()
        self.assertEqual(first.id, job.id)
        second = Job._claim_next_for_worker()
        self.assertFalse(second)

    def test_complete_from_worker_success(self):
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]
        claimed = Job._claim_next_for_worker()
        claimed._complete_from_worker("simulation_completed")
        self.assertEqual(claimed.energyplus_processing_status, "simulation_completed")
        self.assertFalse(claimed.error_message)

    def test_complete_from_worker_failure_records_detail(self):
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]
        claimed = Job._claim_next_for_worker()
        claimed._complete_from_worker("simulation_failed", detail="EnergyPlus fatal error in eplusout.err")
        self.assertEqual(claimed.energyplus_processing_status, "simulation_failed")
        self.assertEqual(claimed.error_message, "EnergyPlus fatal error in eplusout.err")

    def test_complete_from_worker_rejects_job_not_currently_claimed(self):
        """A worker cannot 'complete' a job it never claimed (still
        queued_for_worker) nor one that already finished — this is the
        transition guard the /energyplus-jobs/<id>/complete route relies on
        to turn a state mismatch into a 409 instead of silently accepting a
        stale/duplicate report."""
        job = self._create_queued_energyplus_job()
        with self.assertRaises(UserError):
            job._complete_from_worker("simulation_completed")

        Job = self.env["greencube.cooling.calculation.job"]
        claimed = Job._claim_next_for_worker()
        claimed._complete_from_worker("simulation_completed")
        with self.assertRaises(UserError):
            claimed._complete_from_worker("simulation_completed")

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def test_cancel_energyplus_while_queued_succeeds(self):
        job = self._create_queued_energyplus_job()
        job.action_cancel_energyplus()
        self.assertEqual(job.energyplus_processing_status, "cancelled")

    def test_cancel_energyplus_after_claim_is_rejected(self):
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]
        claimed = Job._claim_next_for_worker()
        with self.assertRaises(UserError):
            claimed.action_cancel_energyplus()
        # Still running, not silently cancelled.
        self.assertEqual(claimed.energyplus_processing_status, "simulation_running")

    def test_cancel_energyplus_after_completion_is_rejected(self):
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]
        claimed = Job._claim_next_for_worker()
        claimed._complete_from_worker("simulation_completed")
        with self.assertRaises(UserError):
            claimed.action_cancel_energyplus()

    # ------------------------------------------------------------------
    # Stall detection / retry / dead-letter
    # ------------------------------------------------------------------

    def _age_claimed_at(self, job, seconds_ago):
        # Flush first: this bypasses the ORM with raw SQL, so any pending
        # (not-yet-flushed) write from the claim just done — e.g.
        # energyplus_processing_status/attempt_count — must already be in
        # the actual table, or the ORM search in
        # _requeue_stalled_energyplus_jobs() could miss this row entirely
        # once its own cache is invalidated below.
        self.env.flush_all()
        stale = fields.Datetime.now() - datetime.timedelta(seconds=seconds_ago)
        self.env.cr.execute(
            "UPDATE greencube_cooling_calculation_job SET claimed_at = %s WHERE id = %s",
            (stale, job.id),
        )
        job.invalidate_recordset()

    def test_requeue_stalled_jobs_requeues_under_max_attempts(self):
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]
        claimed = Job._claim_next_for_worker()
        self.assertEqual(claimed.attempt_count, 1)
        self._age_claimed_at(claimed, seconds_ago=10000)  # far beyond the default 900s stall timeout

        stalled = Job._requeue_stalled_energyplus_jobs()
        self.assertIn(claimed.id, stalled.ids)
        claimed.invalidate_recordset()
        self.assertEqual(claimed.energyplus_processing_status, "queued_for_worker")
        self.assertFalse(claimed.claimed_at)
        # attempt_count is NOT reset — it is what eventually trips dead-letter.
        self.assertEqual(claimed.attempt_count, 1)

    def test_requeue_stalled_jobs_dead_letters_after_max_attempts(self):
        job = self._create_queued_energyplus_job()
        job.write({"max_attempt_count": 2})
        Job = self.env["greencube.cooling.calculation.job"]

        # Attempt 1: claim, stall, requeue.
        claimed = Job._claim_next_for_worker()
        self.assertEqual(claimed.attempt_count, 1)
        self._age_claimed_at(claimed, seconds_ago=10000)
        Job._requeue_stalled_energyplus_jobs()
        claimed.invalidate_recordset()
        self.assertEqual(claimed.energyplus_processing_status, "queued_for_worker")

        # Attempt 2: claim again, stall again -> now at max_attempt_count,
        # so this must be a permanent failure (dead-letter), not another
        # requeue.
        reclaimed = Job._claim_next_for_worker()
        self.assertEqual(reclaimed.id, claimed.id)
        self.assertEqual(reclaimed.attempt_count, 2)
        self._age_claimed_at(reclaimed, seconds_ago=10000)
        Job._requeue_stalled_energyplus_jobs()
        reclaimed.invalidate_recordset()
        self.assertEqual(reclaimed.energyplus_processing_status, "simulation_failed")
        self.assertIn("dead-letter", reclaimed.error_message)

    def test_requeue_stalled_jobs_ignores_fresh_claims(self):
        job = self._create_queued_energyplus_job()
        Job = self.env["greencube.cooling.calculation.job"]
        claimed = Job._claim_next_for_worker()
        # claimed_at is "now" — well within the stall timeout.
        stalled = Job._requeue_stalled_energyplus_jobs()
        self.assertNotIn(claimed.id, stalled.ids)
        claimed.invalidate_recordset()
        self.assertEqual(claimed.energyplus_processing_status, "simulation_running")

    def test_stall_timeout_seconds_config_parameter_override(self):
        Job = self.env["greencube.cooling.calculation.job"]
        self.env["ir.config_parameter"].sudo().set_param(
            "greencube_cooling.energyplus_stall_timeout_seconds", "5"
        )
        self.assertEqual(Job._stall_timeout_seconds(self.env), 5)

        job = self._create_queued_energyplus_job()
        claimed = Job._claim_next_for_worker()
        self._age_claimed_at(claimed, seconds_ago=30)  # well past the 5s override, would not trip the 900s default
        stalled = Job._requeue_stalled_energyplus_jobs()
        self.assertIn(claimed.id, stalled.ids)

    # ------------------------------------------------------------------
    # Write guard on finished jobs
    # ------------------------------------------------------------------

    def test_finished_job_core_fields_are_immutable(self):
        study = self._create_ready_study()
        study.action_create_snapshot()
        result = study.action_calculate()
        job = self.env["greencube.cooling.calculation.job"].search([("result_id", "=", result.id)], limit=1)
        self.assertEqual(job.status, "completed")
        with self.assertRaises(UserError):
            job.write({"status": "failed"})

    def test_finished_job_still_allows_energyplus_handoff_fields(self):
        """A MERCURE job (status=completed) can still legitimately have its
        *independent* EnergyPlus hand-off fields change afterwards — MERCURE
        finishing does not mean the EnergyPlus side (if requested) is done
        too."""
        job = self._create_queued_energyplus_job()
        self.assertEqual(job.status, "completed")  # MERCURE side is done...
        self.assertEqual(job.energyplus_processing_status, "queued_for_worker")  # ...EnergyPlus side is not.
        job.action_cancel_energyplus()  # must not raise
        self.assertEqual(job.energyplus_processing_status, "cancelled")
