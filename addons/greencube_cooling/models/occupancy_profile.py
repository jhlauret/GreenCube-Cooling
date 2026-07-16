# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GreencubeCoolingOccupancyProfile(models.Model):
    _name = "greencube.cooling.occupancy.profile"
    _description = "GreenCube Cooling Occupancy Profile"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    usage_type = fields.Selection(
        [
            ("office", "Office"),
            ("housing", "Housing"),
            ("meeting_room", "Meeting room"),
            ("retail", "Retail"),
            ("workshop", "Workshop"),
            ("medical", "Medical"),
            ("server_room", "Server room"),
            ("other", "Other"),
        ],
        required=True,
        default="office",
    )
    usual_occupants = fields.Integer(default=2)
    maximum_occupants = fields.Integer(default=4)
    activity_level = fields.Selection(
        [
            ("rest", "Rest"),
            ("seated", "Seated"),
            ("light", "Light"),
            ("moderate", "Moderate"),
            ("high", "High"),
        ],
        default="moderate",
    )
    usage_days = fields.Char(default="Mon-Fri")
    start_hour = fields.Float(default=8.0)
    end_hour = fields.Float(default=18.0)
    used_at_night = fields.Boolean(default=False)
    sensible_gain_per_person_w = fields.Float(default=75.0)
    latent_gain_per_person_g_h = fields.Float(default=60.0)
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

    @api.constrains("usual_occupants", "maximum_occupants")
    def _check_occupants(self):
        for line in self:
            if line.usual_occupants < 0 or line.maximum_occupants < 0:
                raise ValidationError("Occupant counts must not be negative.")
            if line.maximum_occupants < line.usual_occupants:
                raise ValidationError("Maximum occupants must be >= usual occupants.")

    @api.constrains("start_hour", "end_hour")
    def _check_hours(self):
        for line in self:
            if not (0 <= line.start_hour <= 24) or not (0 <= line.end_hour <= 24):
                raise ValidationError("Occupancy hours must be between 0 and 24.")

    @api.constrains("sensible_gain_per_person_w", "latent_gain_per_person_g_h")
    def _check_gains(self):
        for line in self:
            if line.sensible_gain_per_person_w < 0 or line.latent_gain_per_person_g_h < 0:
                raise ValidationError("Per-person gains must not be negative.")
