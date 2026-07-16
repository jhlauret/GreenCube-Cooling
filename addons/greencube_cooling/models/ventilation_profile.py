# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GreencubeCoolingVentilationProfile(models.Model):
    _name = "greencube.cooling.ventilation.profile"
    _description = "GreenCube Cooling Ventilation Profile"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    ventilation_type = fields.Selection(
        [
            ("natural", "Natural"),
            ("simple_flow", "Simple flow"),
            ("double_flow", "Double flow"),
            ("dedicated_mechanical", "Dedicated mechanical"),
        ],
        default="simple_flow",
        required=True,
    )
    airflow_m3h = fields.Float(default=60.0)
    air_changes_per_hour = fields.Float(default=1.0)
    heat_recovery_efficiency_percent = fields.Float(default=0.0)
    door_opening_frequency = fields.Selection(
        [("rare", "Rare"), ("occasional", "Occasional"), ("frequent", "Frequent"), ("continuous", "Continuous")],
        default="occasional",
    )
    window_opening_frequency = fields.Selection(
        [("rare", "Rare"), ("occasional", "Occasional"), ("frequent", "Frequent"), ("continuous", "Continuous")],
        default="occasional",
    )
    airtightness_n50 = fields.Float()
    infiltration_ach = fields.Float(default=0.5)
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

    @api.constrains("airflow_m3h", "air_changes_per_hour", "infiltration_ach")
    def _check_flows(self):
        for line in self:
            if line.airflow_m3h < 0 or line.air_changes_per_hour < 0 or line.infiltration_ach < 0:
                raise ValidationError("Airflow values must not be negative.")

    @api.constrains("heat_recovery_efficiency_percent")
    def _check_recovery(self):
        for line in self:
            if not (0 <= line.heat_recovery_efficiency_percent <= 100):
                raise ValidationError("Heat recovery efficiency must be between 0 and 100.")
