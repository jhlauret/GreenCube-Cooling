# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class GreencubeCoolingCalculationJob(models.Model):
    """Serializable calculation job record (GC-COOLING-15 pt.1): what the
    API's `job_id` actually refers to, instead of reusing a
    greencube.cooling.result id as a stand-in job id. MERCURE (quick_solver)
    still runs synchronously inline in action_calculate() — only its
    tracking is now a real row here — but this is also the anchor EnergyPlus
    jobs attach their simulation.artifact records to once the standalone
    `energyplus_worker/` process (outside this Odoo process, no direct
    PostgreSQL access) claims and completes them via the
    /energyplus-jobs/claim and /energyplus-jobs/<id>/complete HTTP routes
    (controllers/api.py). There used to be an in-process cron doing this
    directly against the ORM — removed because it ran with full DB access
    in the same process as the web/cron workers, which is exactly what
    GC-COOLING-15's worker-isolation requirement rules out."""

    _name = "greencube.cooling.calculation.job"
    _description = "GreenCube Cooling Calculation Job"
    _order = "create_date desc"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    snapshot_id = fields.Many2one(
        "greencube.cooling.calculation.snapshot", required=True, ondelete="restrict", index=True
    )
    requested_engine = fields.Selection(
        [("quick_solver", "Quick solver (MERCURE)"), ("energyplus", "EnergyPlus"), ("both", "Both")],
        required=True,
    )
    status = fields.Selection(
        [("queued", "Queued"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")],
        default="queued",
        required=True,
    )
    result_id = fields.Many2one("greencube.cooling.result", ondelete="set null")
    idempotency_key = fields.Char(index=True)
    error_message = fields.Char()
    started_at = fields.Datetime()
    finished_at = fields.Datetime()
    duration_ms = fields.Integer()

    # EnergyPlus is never executed inline by action_calculate — only the
    # (real, tested) Honeybee JSON translation is attempted there. Actual
    # simulation execution belongs to the standalone energyplus_worker/
    # process, which claims/completes jobs only through the HTTP routes in
    # controllers/api.py and never touches this database directly. This
    # field tracks that hand-off independently of the job's own
    # status/result_id, since MERCURE can complete while the EnergyPlus
    # side is still pending.
    energyplus_processing_status = fields.Selection(
        [
            ("not_requested", "Not requested"),
            ("disabled", "Feature flag disabled"),
            ("translation_failed", "Honeybee translation failed"),
            ("queued_for_worker", "Translated, queued for worker"),
            ("simulation_running", "Claimed by worker, running"),
            ("simulation_unavailable", "Worker ran, stack unavailable"),
            ("simulation_failed", "Worker ran, simulation failed"),
            ("simulation_completed", "Worker ran, simulation completed"),
        ],
        default="not_requested",
        required=True,
    )
    claimed_at = fields.Datetime(help="Set when a worker claims this job via POST /energyplus-jobs/claim.")

    artifact_ids = fields.One2many("greencube.cooling.simulation.artifact", "job_id")

    _sql_constraints = [
        ("idempotency_key_uniq", "unique(idempotency_key)", "An idempotency key can only be used for one job."),
    ]

    _ENERGYPLUS_HANDOFF_FIELDS = {"energyplus_processing_status", "claimed_at", "error_message"}

    def write(self, vals):
        if any(job.status in ("completed", "failed") for job in self) and not set(vals.keys()) <= self._ENERGYPLUS_HANDOFF_FIELDS:
            # The one exception is the async EnergyPlus hand-off fields,
            # which legitimately change after the job's own (MERCURE)
            # status is already "completed" — everything else about a
            # finished job is historical record.
            raise UserError("A finished calculation job cannot be modified, except its EnergyPlus worker status.")
        return super().write(vals)

    def unlink(self):
        if any(job.status in ("completed", "failed") for job in self):
            raise UserError("A finished calculation job cannot be deleted.")
        return super().unlink()

    def _claim_next_for_worker(self):
        """Atomically hands the oldest queued EnergyPlus job to a worker.
        Called only from the /energyplus-jobs/claim route (controllers/api.py),
        never from inside the Odoo request/cron path that would otherwise
        run the simulation itself — that in-process path is exactly what
        GC-COOLING-15 forbids. Returns None if there is nothing to claim.
        """
        job = self.search([("energyplus_processing_status", "=", "queued_for_worker")], limit=1, order="create_date asc")
        if not job:
            return None
        job.write({"energyplus_processing_status": "simulation_running", "claimed_at": fields.Datetime.now()})
        return job

    def _complete_from_worker(self, status, detail=None):
        """Records the outcome a worker reported for this job via
        POST /energyplus-jobs/<id>/complete. `status` is one of
        simulation_completed/simulation_unavailable/simulation_failed —
        anything else is rejected by the controller before reaching here."""
        self.ensure_one()
        if self.energyplus_processing_status != "simulation_running":
            raise UserError(
                f"Job {self.id} is not currently claimed by a worker "
                f"(status={self.energyplus_processing_status})."
            )
        vals = {"energyplus_processing_status": status}
        if detail and status != "simulation_completed":
            vals["error_message"] = detail
        self.write(vals)
