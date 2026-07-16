# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GreencubeCoolingEquipmentLoad(models.Model):
    _name = "greencube.cooling.equipment.load"
    _description = "GreenCube Cooling Equipment Load"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product")
    name = fields.Char(required=True)
    category = fields.Selection(
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
    )
    quantity = fields.Float(default=1.0)
    unit_power_w = fields.Float(default=0.0)
    usage_hours_per_day = fields.Float(default=8.0)
    simultaneity_percent = fields.Float(default=100.0)
    heat_dissipation_factor = fields.Float(default=1.0)
    permanent_operation = fields.Boolean(default=False)
    provenance = fields.Selection(
        [
            ("catalog", "Catalog"),
            ("api", "API"),
            ("user_confirmed", "User confirmed"),
            ("estimated_reference", "Estimated (reference)"),
            ("estimated_manual", "Estimated (manual)"),
            ("missing_fallback", "Missing (fallback)"),
        ],
        default="catalog",
    )
    notes = fields.Char()
    thermal_load_w = fields.Float(compute="_compute_thermal_load", store=True)

    @api.depends("quantity", "unit_power_w", "simultaneity_percent", "heat_dissipation_factor")
    def _compute_thermal_load(self):
        for line in self:
            line.thermal_load_w = (
                line.quantity * line.unit_power_w * (line.simultaneity_percent / 100.0) * line.heat_dissipation_factor
            )

    @api.constrains("quantity", "unit_power_w", "usage_hours_per_day", "simultaneity_percent", "heat_dissipation_factor")
    def _check_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError("Quantity must be positive.")
            if line.unit_power_w < 0:
                raise ValidationError("Unit power must not be negative.")
            if not (0 <= line.usage_hours_per_day <= 24):
                raise ValidationError("Usage hours must be between 0 and 24.")
            if not (0 <= line.simultaneity_percent <= 100):
                raise ValidationError("Simultaneity must be between 0 and 100.")
            if not (0 <= line.heat_dissipation_factor <= 1):
                raise ValidationError("Heat dissipation factor must be between 0 and 1.")
