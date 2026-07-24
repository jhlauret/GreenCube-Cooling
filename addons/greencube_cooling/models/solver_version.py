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

    def unlink(self):
        # GC-COOLING-01 §16.3: "une version utilisée ne peut pas être
        # supprimée". write() above already blocked touching
        # coefficients_json once used, but unlink() was never guarded, so a
        # manager could still delete a solver version referenced by an
        # existing (immutable) result — orphaning result.solver_version_id
        # and destroying the audit trail of which formulas produced it.
        if any(version.is_used for version in self):
            raise UserError("A solver version used by at least one result cannot be deleted.")
        return super().unlink()

    def _provision_for_companies(self, companies):
        """Ensures every company in `companies` has its own active MERCURE
        solver version, copied from whichever company already has one.

        company_id is required=True here (real per-company data, same
        convention as greencube.thermal.specification) and
        data/solver_version_data.xml only ever creates one row, for the
        company active at install time — so without this, any other
        company in the database could never run a single calculation
        (SOLVER_VERSION_MISSING, found by testing a real non-superuser user
        of a second company). Called from res.company.create() (new
        companies) and from post_init_hook/migrations (existing companies).
        Idempotent: a company that already has one is left untouched.
        """
        reference = self.sudo().search([("code", "=", "MERCURE"), ("state", "=", "active")], limit=1)
        if not reference:
            return
        for company in companies:
            if self.sudo().search([("code", "=", "MERCURE"), ("company_id", "=", company.id)], limit=1):
                continue
            # state must be passed explicitly: Odoo resets any field named
            # "state" to its default on copy() unless told otherwise (see
            # odoo/fields.py, "by default, state fields should be reset on
            # copy") — without this, the provisioned row would silently
            # come out as "draft" and SOLVER_VERSION_MISSING would still
            # fire, defeating the whole point of this method.
            reference.sudo().copy({"company_id": company.id, "state": "active"})

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
