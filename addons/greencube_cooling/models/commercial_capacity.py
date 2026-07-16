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
