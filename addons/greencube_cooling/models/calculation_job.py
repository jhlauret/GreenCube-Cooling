# -*- coding: utf-8 -*-
import datetime
import logging

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# How long a job may sit in simulation_running (claimed by a worker) before
# it is considered stalled — e.g. the worker process crashed or was killed
# mid-simulation without ever calling /energyplus-jobs/<id>/complete. This is
# deliberately a heartbeat-by-proxy: today's worker (energyplus_worker/worker.py)
# makes one blocking claim -> run -> complete call and never pings back
# progress, so `claimed_at` is the only signal we have. A real incremental
# heartbeat would need the worker to report progress mid-run, which is out
# of scope for this pass (see docs referenced in the final report).
DEFAULT_ENERGYPLUS_STALL_TIMEOUT_SECONDS = 900
DEFAULT_ENERGYPLUS_MAX_ATTEMPTS = 3


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
            ("cancelled", "Cancelled before a worker claimed it"),
        ],
        default="not_requested",
        required=True,
    )
    claimed_at = fields.Datetime(help="Set when a worker claims this job via POST /energyplus-jobs/claim.")

    # GC-COOLING-15 pt.2: retry/dead-letter bookkeeping. A job that stalls
    # (claimed but never completed within the timeout) is requeued up to
    # max_attempt_count times, then permanently failed instead of retried
    # forever — see _requeue_stalled_energyplus_jobs() below.
    attempt_count = fields.Integer(default=0, required=True)
    max_attempt_count = fields.Integer(default=DEFAULT_ENERGYPLUS_MAX_ATTEMPTS, required=True)

    artifact_ids = fields.One2many("greencube.cooling.simulation.artifact", "job_id")

    # GC-COOLING-05A pt.10: "Préparer un contrat de job sérialisable pour le
    # futur worker: snapshot_id, solver_version, weather_artifact, options."
    # snapshot_id/requested_engine already exist above; these three fields
    # complete that contract ahead of the actual EnergyPlus worker
    # orchestration (GC-COOLING-15's later, fuller scope). All three are
    # optional and unpopulated by today's inline translation path
    # (_process_energyplus_translation in cooling_study.py) — they exist so
    # a job row can already reference *which* solver version and *which*
    # resolved weather artifact it was built for once that resolution
    # exists, without a further schema change at that point.
    solver_version_id = fields.Many2one(
        "greencube.cooling.solver.version",
        ondelete="restrict",
        help="Which solver/engine version this job was built against, once EnergyPlus jobs are versioned "
        "the same way MERCURE results already are via greencube.cooling.result.solver_version_id.",
    )
    weather_artifact_id = fields.Many2one(
        "greencube.cooling.simulation.artifact",
        ondelete="restrict",
        help="The resolved weather (EPW/design-day) artifact this job's simulation would run against. "
        "Never a client-supplied path or URL (GC-COOLING-05A's SSRF/arbitrary-file rules) — only a "
        "reference to an artifact this server already produced/validated.",
    )
    simulation_options_json = fields.Text(
        default="{}",
        help="Serialized, server-validated simulation options (e.g. simulation mode) for the future worker "
        "contract. Never free-form: this is not a place for an arbitrary IDF/EPJSON template or macro.",
    )

    _sql_constraints = [
        ("idempotency_key_uniq", "unique(idempotency_key)", "An idempotency key can only be used for one job."),
    ]

    _ENERGYPLUS_HANDOFF_FIELDS = {
        "energyplus_processing_status",
        "claimed_at",
        "error_message",
        "attempt_count",
        "max_attempt_count",
    }

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

        Uses `SELECT ... FOR UPDATE SKIP LOCKED` (raw SQL, not an ORM
        search) rather than a plain search+write: if two worker processes
        call /energyplus-jobs/claim concurrently, a plain search could
        return the same job to both before either commits its write,
        letting two workers run the same simulation. SKIP LOCKED makes the
        second concurrent caller skip a row already locked by the first
        transaction instead of blocking or double-claiming it, which is the
        standard Postgres pattern for a single-consumer job queue and is
        the actual "un seul worker doit exécuter un job donné" guarantee —
        the ORM search()+write() pair used before this did not provide it.
        """
        # Raw SQL bypasses the ORM entirely, so any not-yet-flushed ORM
        # write on this model (e.g. a previous claim's own
        # energyplus_processing_status update, still only in the
        # in-memory cache) must be pushed to the actual table first —
        # otherwise this SELECT could still see a job as 'queued_for_worker'
        # in the database even though the ORM already marked it claimed.
        self.env.flush_all()
        self.env.cr.execute(
            """
            SELECT id FROM greencube_cooling_calculation_job
            WHERE energyplus_processing_status = 'queued_for_worker'
            ORDER BY create_date ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )
        row = self.env.cr.fetchone()
        if not row:
            return None
        job = self.browse(row[0])
        job.write(
            {
                "energyplus_processing_status": "simulation_running",
                "claimed_at": fields.Datetime.now(),
                "attempt_count": job.attempt_count + 1,
            }
        )
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

    def action_cancel_energyplus(self):
        """User-initiated cancellation (POST /energyplus-jobs/<id>/cancel).
        Only allowed while the job is still `queued_for_worker` — i.e. no
        worker has claimed it yet. Once a worker has claimed a job
        (`simulation_running`), today's worker makes one blocking,
        uninterruptible call to `run_energyplus_simulation`; there is no
        subprocess handle here to signal, so honestly refusing the
        cancellation (409) is the correct behaviour rather than pretending
        to stop an execution we have no way to reach. This matches the
        spec's "vérifier l'état" requirement — cancellation is a state
        transition guard, not a promise to kill an arbitrary process."""
        self.ensure_one()
        if self.energyplus_processing_status != "queued_for_worker":
            raise UserError(
                f"Job {self.id} cannot be cancelled from state '{self.energyplus_processing_status}' "
                "(only a job still waiting for a worker can be cancelled)."
            )
        self.write({"energyplus_processing_status": "cancelled"})

    @staticmethod
    def _stall_timeout_seconds(env):
        param = env["ir.config_parameter"].sudo().get_param(
            "greencube_cooling.energyplus_stall_timeout_seconds", default=str(DEFAULT_ENERGYPLUS_STALL_TIMEOUT_SECONDS)
        )
        try:
            return max(1, int(param))
        except (TypeError, ValueError):
            return DEFAULT_ENERGYPLUS_STALL_TIMEOUT_SECONDS

    def _requeue_stalled_energyplus_jobs(self):
        """Reclaims jobs a worker claimed but never reported back on within
        the stall timeout — e.g. the worker process (or its host) crashed
        mid-simulation. Requeued up to `max_attempt_count` times; beyond
        that the job is permanently failed (dead-letter) rather than
        retried forever. Intended to run from a lightweight ir.cron — this
        method never runs EnergyPlus itself, only flips job bookkeeping, so
        it does not violate the "never run EnergyPlus in the Odoo web/cron
        process" rule."""
        timeout_s = self._stall_timeout_seconds(self.env)
        cutoff = fields.Datetime.now() - datetime.timedelta(seconds=timeout_s)
        stalled = self.search(
            [
                ("energyplus_processing_status", "=", "simulation_running"),
                ("claimed_at", "!=", False),
                ("claimed_at", "<", cutoff),
            ]
        )
        for job in stalled:
            if job.attempt_count >= job.max_attempt_count:
                job.write(
                    {
                        "energyplus_processing_status": "simulation_failed",
                        "error_message": (
                            f"Stalled: no heartbeat from worker for over {timeout_s}s after "
                            f"{job.attempt_count} attempt(s); giving up (dead-letter)."
                        ),
                    }
                )
                _logger.warning("EnergyPlus job %s dead-lettered after %s stalled attempts.", job.id, job.attempt_count)
            else:
                job.write({"energyplus_processing_status": "queued_for_worker", "claimed_at": False})
                _logger.warning("EnergyPlus job %s stalled, requeued (attempt %s).", job.id, job.attempt_count)
        return stalled
