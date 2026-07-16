# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_cooling_equipment = fields.Boolean(default=False, help="Exposed in the GreenCube Cooling equipment catalog.")
    cooling_equipment_type = fields.Selection(
        [("split_wall", "Split (wall)"), ("multi_split", "Multi-split"), ("ducted", "Ducted"), ("portable", "Portable")]
    )
    nominal_capacity_w = fields.Float()
    capacity_at_35c_w = fields.Float()
    capacity_at_45c_w = fields.Float()
    electrical_power_w = fields.Float()
    eer = fields.Float(digits=(6, 2))
    seer = fields.Float(digits=(6, 2))
    cooling_shr = fields.Float(digits=(4, 3))
    noise_db = fields.Float()
    max_outdoor_temperature_c = fields.Float()
    power_supply = fields.Selection([("monophase", "Single-phase"), ("triphase", "Three-phase")])
    data_quality = fields.Selection(
        [("catalog", "Catalog"), ("estimated", "Estimated"), ("missing", "Missing")], default="catalog"
    )
