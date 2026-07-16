# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class GreencubeCoolingResultComponent(models.Model):
    _name = "greencube.cooling.result.component"
    _description = "GreenCube Cooling Result Component"
    _order = "total_w desc"

    result_id = fields.Many2one("greencube.cooling.result", required=True, ondelete="cascade", index=True)
    component_code = fields.Char(required=True)
    label = fields.Char(required=True)
    sensible_w = fields.Float()
    latent_w = fields.Float()
    total_w = fields.Float()
    percentage_of_total = fields.Float(digits=(6, 2))

    @api.constrains("sensible_w", "latent_w", "percentage_of_total")
    def _check_values(self):
        for line in self:
            if line.sensible_w < 0 or line.latent_w < 0:
                raise ValidationError("Component loads must not be negative.")
            if not (-0.01 <= line.percentage_of_total <= 100.01):
                raise ValidationError("percentage_of_total must be between 0 and 100.")

    def write(self, vals):
        raise UserError("Result components are immutable once created.")

    def unlink(self):
        raise UserError("Result components cannot be deleted individually.")
