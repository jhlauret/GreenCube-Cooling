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

    # Internal-loads (equipment/lighting/appliances) catalog, distinct from
    # the cooling-equipment-to-install catalog above. GC-COOLING-11 audit:
    # the Equipment step's list of offered internal-load templates (laptop,
    # monitor, server, ...) used to be a static array hardcoded in the
    # frontend, so it never came from Odoo and could never be extended or
    # corrected without a frontend deploy. These fields let a
    # product.template be exposed instead as a real, versionable catalog
    # entry for that screen.
    is_internal_load_equipment = fields.Boolean(
        default=False, help="Exposed in the GreenCube Cooling internal-loads (equipment/lighting) catalog."
    )
    internal_load_code = fields.Char(
        help="Stable catalog code (e.g. 'laptop') used by the frontend to recognize a line across saves, "
        "independently of the product's (possibly translated/edited) name."
    )
    internal_load_category = fields.Selection(
        [
            ("it", "IT"),
            ("lighting", "Lighting"),
            ("appliance", "Appliance"),
            ("kitchen", "Kitchen"),
            ("network", "Network"),
            ("battery", "Battery"),
            ("inverter", "Inverter"),
            ("medical", "Medical"),
            ("machine", "Machine"),
            ("other", "Other"),
        ],
        default="other",
        help="Must stay aligned with greencube.cooling.equipment.load.category.",
    )
    internal_load_unit_power_w = fields.Float(help="Reference nominal power per unit, in watts.")
    internal_load_usage_hours_per_day = fields.Float(help="Reference average daily usage, in hours (0-24).")
    internal_load_simultaneity_percent = fields.Float(
        default=100.0, help="Reference simultaneity factor, in percent (0-100)."
    )
