# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GreencubeCoolingShading(models.Model):
    _name = "greencube.cooling.shading"
    _description = "GreenCube Cooling Solar Shading"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    orientation = fields.Selection(
        [
            ("north", "North"),
            ("north_east", "North-East"),
            ("east", "East"),
            ("south_east", "South-East"),
            ("south", "South"),
            ("south_west", "South-West"),
            ("west", "West"),
            ("north_west", "North-West"),
        ],
        required=True,
    )
    shading_type = fields.Selection(
        [
            ("none", "None"),
            ("internal_blind", "Internal blind"),
            ("external_blind", "External blind"),
            ("brise_soleil", "Brise-soleil"),
            ("overhang", "Overhang"),
            ("natural", "Natural shading"),
            ("building", "Neighbouring building"),
            ("mountain", "Mountain mask"),
        ],
        default="none",
    )
    efficiency_percent = fields.Float(default=0.0)
    start_hour = fields.Float(default=0.0)
    end_hour = fields.Float(default=24.0)
    automatic = fields.Boolean(default=False)
    confirmed = fields.Boolean(default=False)
    provenance = fields.Selection(
        [
            ("catalog", "Catalog"),
            ("api", "API"),
            ("user_confirmed", "User confirmed"),
            ("estimated_reference", "Estimated (reference)"),
            ("estimated_manual", "Estimated (manual)"),
            ("missing_fallback", "Missing (fallback)"),
        ],
        default="user_confirmed",
    )

    @api.constrains("efficiency_percent")
    def _check_efficiency(self):
        for line in self:
            if not (0 <= line.efficiency_percent <= 100):
                raise ValidationError("Efficiency must be between 0 and 100.")

    @api.constrains("start_hour", "end_hour")
    def _check_hours(self):
        for line in self:
            if not (0 <= line.start_hour <= 24) or not (0 <= line.end_hour <= 24):
                raise ValidationError("Hours must be between 0 and 24.")
            if line.end_hour < line.start_hour:
                raise ValidationError("End hour must not be before start hour.")
