# -*- coding: utf-8 -*-
import json
import logging

from odoo import fields, models
from odoo.exceptions import UserError

from ..services.energyplus import EnergyPlusSimulationError, EnergyPlusUnavailableError, run_energyplus_simulation
from ..services.mercure.serialization import mercure_input_from_dict

_logger = logging.getLogger(__name__)


class GreencubeCoolingCalculationJob(models.Model):
    """Serializable calculation job record (GC-COOLING-15 pt.1): what the
    API's `job_id` actually refers to, instead of reusing a
    greencube.cooling.result id as a stand-in job id. MERCURE (quick_solver)
    still runs synchronously inline in action_calculate() — only its
    tracking is now a real row here — but this is also the anchor future
    EnergyPlus jobs attach their simulation.artifact records to once a real
    worker (see the cron in data/energyplus_cron_data.xml) picks them up."""

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
    # simulation execution belongs to the cron-driven worker
    # (_cron_process_pending_energyplus_jobs), which is the only place
    # allowed to call services.energyplus.run_energyplus_simulation. This
    # field tracks that hand-off independently of the job's own
    # status/result_id, since MERCURE can complete while the EnergyPlus
    # side is still pending.
    energyplus_processing_status = fields.Selection(
        [
            ("not_requested", "Not requested"),
            ("disabled", "Feature flag disabled"),
            ("translation_failed", "Honeybee translation failed"),
            ("queued_for_worker", "Translated, queued for worker"),
            ("simulation_unavailable", "Worker ran, stack unavailable"),
            ("simulation_failed", "Worker ran, simulation failed"),
            ("simulation_completed", "Worker ran, simulation completed"),
        ],
        default="not_requested",
        required=True,
    )

    artifact_ids = fields.One2many("greencube.cooling.simulation.artifact", "job_id")

    _sql_constraints = [
        ("idempotency_key_uniq", "unique(idempotency_key)", "An idempotency key can only be used for one job."),
    ]

    def write(self, vals):
        if any(job.status in ("completed", "failed") for job in self) and set(vals.keys()) != {
            "energyplus_processing_status"
        }:
            # The one exception is the async EnergyPlus hand-off field,
            # which legitimately changes after the job's own (MERCURE)
            # status is already "completed" — everything else about a
            # finished job is historical record.
            raise UserError("A finished calculation job cannot be modified, except its EnergyPlus worker status.")
        return super().write(vals)

    def unlink(self):
        if any(job.status in ("completed", "failed") for job in self):
            raise UserError("A finished calculation job cannot be deleted.")
        return super().unlink()

    def _cron_process_pending_energyplus_jobs(self, batch_size=20):
        """Cron entry point (data/energyplus_cron_data.xml). This is the
        ONLY place allowed to call services.energyplus.run_energyplus_simulation
        — cooling_study.py's action_calculate() never does, precisely so the
        actual EnergyPlus binary invocation stays out of the HTTP request/
        web-worker path (GC-COOLING-15's worker-isolation requirement).
        Today this always ends in "unavailable" or "not implemented" (see
        services/energyplus.py's own docstring) since neither the
        honeybee-energy/ladybug packages nor the EnergyPlus binary are
        expected to be present — that is the honest, current end state of
        the pipeline, not a placeholder pretending otherwise.
        """
        jobs = self.search([("energyplus_processing_status", "=", "queued_for_worker")], limit=batch_size)
        for job in jobs:
            try:
                mercure_input = mercure_input_from_dict(json.loads(job.snapshot_id.payload_json))
                run_energyplus_simulation(mercure_input)
                job.write({"energyplus_processing_status": "simulation_completed"})
            except EnergyPlusUnavailableError:
                job.write({"energyplus_processing_status": "simulation_unavailable"})
            except EnergyPlusSimulationError:
                job.write({"energyplus_processing_status": "simulation_failed"})
            except Exception:
                _logger.exception("Unexpected error processing EnergyPlus job %s", job.id)
                job.write({"energyplus_processing_status": "simulation_failed"})
