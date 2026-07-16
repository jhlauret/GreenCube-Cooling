# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class GreencubeCoolingSolverVersion(models.Model):
    _name = "greencube.cooling.solver.version"
    _description = "GreenCube Cooling Solver Version"
    _sql_constraints = [
        ("code_version_company_uniq", "unique(code, version, company_id)", "A solver code/version must be unique per company."),
    ]

    name = fields.Char(required=True)
    code = fields.Char(required=True, default="MERCURE")
    version = fields.Char(required=True, default="1.0.0")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("retired", "Retired")], default="draft", required=True
    )
    formula_description = fields.Html()
    coefficients_json = fields.Text(default="{}")
    valid_from = fields.Date()
    valid_to = fields.Date()
    checksum = fields.Char(readonly=True)
    notes = fields.Char()

    result_ids = fields.One2many("greencube.cooling.result", "solver_version_id")
    is_used = fields.Boolean(compute="_compute_is_used")

    def _compute_is_used(self):
        for version in self:
            version.is_used = bool(version.result_ids)

    def write(self, vals):
        for version in self:
            if version.is_used and "coefficients_json" in vals:
                raise UserError("A solver version already used by a result cannot have its coefficients modified.")
        return super().write(vals)

    @api.constrains("state", "code", "company_id")
    def _check_single_active(self):
        for version in self:
            if version.state != "active":
                continue
            others = self.search(
                [
                    ("code", "=", version.code),
                    ("company_id", "=", version.company_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", version.id),
                ]
            )
            if others:
                raise UserError(f"Another active version already exists for solver {version.code}.")
