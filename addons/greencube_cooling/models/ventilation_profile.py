# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.mercure.constants import OPENING_FREQUENCY_ACH_INCREMENT
from ..services.mercure.conversions import ach_from_n50


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
    airtightness_n50 = fields.Float(
        help="Measured or estimated air changes per hour at 50 Pa (EN 13829). "
        "0 means no n50 value is available; infiltration_ach is then used as-is."
    )
    wind_exposure = fields.Selection(
        [
            ("sheltered", "Sheltered"),
            ("normal", "Normal"),
            ("exposed", "Exposed"),
            ("very_exposed", "Very exposed"),
        ],
        default="normal",
        required=True,
        help="Used only to convert airtightness_n50 into a natural infiltration rate "
        "(see get_effective_infiltration_ach). Has no effect when airtightness_n50 is 0.",
    )
    infiltration_ach = fields.Float(
        default=0.5,
        help="Manually entered natural infiltration rate, used as-is whenever "
        "airtightness_n50 is 0. Ignored (superseded by the n50-derived value) once "
        "airtightness_n50 is set — see get_effective_infiltration_ach().",
    )
    fan_power_w = fields.Float(default=30.0)
    fan_fraction_dissipated_in_zone = fields.Float(
        default=1.0,
        help="Share (0-1) of the ventilation fan's electrical power that ends up as "
        "sensible heat inside the conditioned zone (GC-COOLING-14: was previously "
        "hardcoded to 1.0 in every study regardless of this profile, silently "
        "ignoring cases like a dedicated_mechanical/double_flow AHU whose motor "
        "sits outside the zone, e.g. on a roof or in an unconditioned plant room). "
        "1.0 is still correct for a typical in-room simple_flow/natural exhaust "
        "fan; lower it when the fan itself is not in the cooled space.",
    )
    bypass_active = fields.Boolean(
        default=False, help="Summer bypass of the heat recovery exchanger: fresh air is no longer preheated/precooled."
    )
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

    @api.constrains("fan_fraction_dissipated_in_zone")
    def _check_fan_fraction_dissipated_in_zone(self):
        for line in self:
            if not (0 <= line.fan_fraction_dissipated_in_zone <= 1):
                raise ValidationError("fan_fraction_dissipated_in_zone must be between 0 and 1.")

    @api.constrains("airtightness_n50")
    def _check_airtightness_n50(self):
        for line in self:
            if not (0 <= line.airtightness_n50 <= 30):
                raise ValidationError("airtightness_n50 must be between 0 and 30 vol/h at 50 Pa.")

    def get_effective_infiltration_ach(self):
        """Single, documented source of truth for the natural infiltration
        rate actually sent to the solver (GC-COOLING-12).

        Precedence: airtightness_n50 (converted via the shared
        ach_from_n50/wind_exposure method) when set, otherwise the manually
        entered infiltration_ach. On top of whichever baseline is used, adds
        the estimated extra air exchange from voluntary door/window opening
        (see OPENING_FREQUENCY_ACH_INCREMENT) — a distinct, additive air path,
        not a re-statement of the same infiltration figure.
        """
        self.ensure_one()
        base = (
            ach_from_n50(self.airtightness_n50, self.wind_exposure)
            if self.airtightness_n50 > 0
            else max(self.infiltration_ach, 0.0)
        )
        opening_increment = OPENING_FREQUENCY_ACH_INCREMENT.get(
            self.door_opening_frequency, 0.0
        ) + OPENING_FREQUENCY_ACH_INCREMENT.get(self.window_opening_frequency, 0.0)
        return base + opening_increment

    def write(self, vals):
        # Mirrors greencube.cooling.study.LOCKED_STATES / occupancy_profile's
        # own guard: a validated study is a frozen record end-to-end, so
        # ventilation/infiltration/comfort inputs must not be editable in
        # place either — a revision is required (GC-COOLING-12 audit gap:
        # this model had no lock at all before, unlike occupancy_profile).
        for line in self:
            if line.study_id.state == "validated" and set(vals.keys()) - {"provenance"}:
                raise UserError(
                    "This study is validated and locked. Create a revision to change its ventilation data."
                )
        return super().write(vals)

    def unlink(self):
        if any(line.study_id.state == "validated" for line in self):
            raise UserError(
                "Ventilation data of a validated study cannot be deleted directly; create a revision instead."
            )
        return super().unlink()
