# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class GreencubeCoolingResult(models.Model):
    _name = "greencube.cooling.result"
    _description = "GreenCube Cooling Result"
    _order = "create_date desc"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    snapshot_id = fields.Many2one("greencube.cooling.calculation.snapshot", ondelete="restrict", index=True)
    solver_version_id = fields.Many2one("greencube.cooling.solver.version")
    state = fields.Selection(
        [("success", "Success"), ("partial", "Partial"), ("failed", "Failed"), ("superseded", "Superseded")],
        default="success",
        required=True,
    )

    governing_scenario_code = fields.Selection(
        [
            ("reference_summer", "Été de référence"),
            ("hot_weather", "Forte chaleur"),
            ("prolonged_heatwave", "Canicule prolongée"),
        ]
    )
    sensible_load_w = fields.Float()
    latent_load_w = fields.Float()
    total_load_w = fields.Float()
    shr = fields.Float(digits=(4, 3))
    margin_w = fields.Float()
    recommended_capacity_w = fields.Float()
    recommended_capacity_kw = fields.Float(digits=(8, 3))
    recommended_capacity_btu_h = fields.Float()
    confidence_score = fields.Float(digits=(4, 3))
    warnings_json = fields.Text()
    main_load_drivers_json = fields.Text()
    duration_ms = fields.Integer()
    snapshot_hash = fields.Char(index=True)
    idempotency_key = fields.Char(index=True)

    component_ids = fields.One2many("greencube.cooling.result.component", "result_id")

    _sql_constraints = [
        ("idempotency_key_uniq", "unique(idempotency_key)", "An idempotency key can only be used for one result."),
    ]

    def write(self, vals):
        allowed = {"state"} if set(vals.keys()) <= {"state"} and vals.get("state") == "superseded" else set()
        if set(vals.keys()) - allowed:
            raise UserError("A calculation result is immutable once created.")
        return super().write(vals)

    def unlink(self):
        raise UserError("A calculation result cannot be deleted.")
