# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class GreencubeCoolingCalculationSnapshot(models.Model):
    _name = "greencube.cooling.calculation.snapshot"
    _description = "GreenCube Cooling Calculation Snapshot"
    _order = "create_date desc"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="study_id.company_id", store=True, index=True)
    study_revision_number = fields.Integer(required=True)
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)

    thermal_specification_id = fields.Many2one("greencube.thermal.specification", required=True, ondelete="restrict")
    thermal_specification_version = fields.Char(required=True)

    requested_engine = fields.Selection(
        [("quick_solver", "Quick solver (MERCURE)"), ("energyplus", "EnergyPlus"), ("both", "Both")],
        default="quick_solver",
        required=True,
    )
    scenario_codes_json = fields.Char(required=True)
    payload_json = fields.Text(required=True, help="Frozen MercureInput, as produced by services.mercure.serialization.")
    confirmed_assumptions_json = fields.Text(help="Provenance breakdown of the study's sub-lines at freeze time.")
    snapshot_hash = fields.Char(required=True, index=True)

    state = fields.Selection(
        [("frozen", "Frozen"), ("superseded", "Superseded")], default="frozen", required=True
    )

    result_ids = fields.One2many("greencube.cooling.result", "snapshot_id")

    _sql_constraints = [
        ("snapshot_hash_uniq", "unique(snapshot_hash)", "A snapshot hash must be unique."),
    ]

    def write(self, vals):
        allowed = {"state"} if set(vals.keys()) <= {"state"} and vals.get("state") == "superseded" else set()
        if set(vals.keys()) - allowed:
            raise UserError("A calculation snapshot is immutable once created.")
        return super().write(vals)

    def unlink(self):
        raise UserError("A calculation snapshot cannot be deleted.")
