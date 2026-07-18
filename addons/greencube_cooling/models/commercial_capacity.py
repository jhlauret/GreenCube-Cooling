# -*- coding: utf-8 -*-
from odoo import fields, models

BTU_PER_KW = 3412.142


class GreencubeCoolingCommercialCapacity(models.Model):
    _name = "greencube.cooling.commercial.capacity"
    _description = "GreenCube Cooling Commercial Capacity Tier"
    _order = "sequence, capacity_btu_h"

    name = fields.Char(required=True)
    capacity_btu_h = fields.Float(required=True)
    capacity_kw = fields.Float(compute="_compute_capacity_kw", store=True)
    active = fields.Boolean(default=True)
    min_load_w = fields.Float()
    max_load_w = fields.Float()
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    def _compute_capacity_kw(self):
        for rec in self:
            rec.capacity_kw = rec.capacity_btu_h / BTU_PER_KW

    def find_tier_for_load_w(self, load_w):
        """Return the smallest active commercial tier whose capacity covers load_w (W),
        or the largest tier if load_w exceeds every tier."""
        if load_w <= 0:
            return self.browse()
        watts_per_btu_h = 1000.0 / BTU_PER_KW
        tiers = self.search([("active", "=", True)])
        covering = tiers.filtered(lambda t: t.capacity_btu_h * watts_per_btu_h >= load_w)
        if covering:
            return covering[0]
        return tiers[-1:] if tiers else self.browse()
