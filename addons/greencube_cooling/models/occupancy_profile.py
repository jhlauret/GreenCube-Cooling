# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

WEEKDAY_FIELDS = (
    "active_monday",
    "active_tuesday",
    "active_wednesday",
    "active_thursday",
    "active_friday",
    "active_saturday",
    "active_sunday",
)


class GreencubeCoolingOccupancyProfile(models.Model):
    _name = "greencube.cooling.occupancy.profile"
    _description = "GreenCube Cooling Occupancy Profile"

    # GC-COOLING-10: this model is per-study (study_id required, One2many
    # study.occupancy_profile_ids) but every consumer (cooling_study.py's
    # MERCURE input builder, the /occupancy-profile API route) still only
    # ever reads occupancy_profile_ids[:1] -- a single global occupancy
    # profile per study/revision. The One2many relation is deliberately
    # kept (rather than a Many2one/singleton) so a future multi-zone model
    # can add more lines without a schema migration, but the MVP does not
    # attempt to reconcile multiple lines: only the first is authoritative.
    # This is the "documenter explicitement un profil global unique"
    # simplification called out in README_GC-COOLING-10.
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
    # Structured weekly calendar (GC-COOLING-10): replaces the previous
    # free-text `usage_days` ("Mon-Fri") as the source of truth, since a
    # free-text string can neither be validated nor safely consumed by the
    # solver or Honeybee/EnergyPlus mapping ("Ne pas stocker le planning en
    # texte libre" — README §"Format des horaires"). `usage_days` is kept
    # below, unmodified, as a legacy/display-only field for any older
    # client still reading it; it is no longer written by new code and no
    # longer read by the MERCURE input builder.
    active_monday = fields.Boolean(default=True, string="Monday")
    active_tuesday = fields.Boolean(default=True, string="Tuesday")
    active_wednesday = fields.Boolean(default=True, string="Wednesday")
    active_thursday = fields.Boolean(default=True, string="Thursday")
    active_friday = fields.Boolean(default=True, string="Friday")
    active_saturday = fields.Boolean(default=False, string="Saturday")
    active_sunday = fields.Boolean(default=False, string="Sunday")
    usage_days = fields.Char(
        default="Mon-Fri",
        help="Legacy free-text summary, display-only. The authoritative weekly "
        "calendar is the active_<weekday> boolean fields.",
    )
    active_days_count = fields.Integer(compute="_compute_schedule", store=True)
    start_hour = fields.Float(default=8.0)
    end_hour = fields.Float(default=18.0)
    # Whether the daily window crosses midnight (e.g. 22:00 -> 06:00): the
    # occupied duration is then (24 - start_hour) + end_hour rather than
    # end_hour - start_hour (README §"Passage de minuit"). MERCURE only
    # needs the resulting duration/fraction, not the crossing itself, but
    # this is exposed so the frontend can show an explicit indicator
    # instead of silently computing (and possibly getting wrong) a
    # negative duration.
    crosses_midnight = fields.Boolean(compute="_compute_schedule", store=True)
    daily_occupied_hours = fields.Float(compute="_compute_schedule", store=True)
    # Average fraction of the day the space is occupied, derived from
    # start_hour/end_hour exactly like equipment_load's own
    # usage_hours_per_day / 24 "operating_fraction" convention (see
    # models/cooling_study.py's MERCURE input builder and
    # services/mercure/engine.py's _equipment_gains) -- this is the same
    # steady-state daily-average simplification already used for
    # equipment and lighting, not a new methodology invented for
    # occupancy. Feeds Occupancy.occupancy_fraction in the MERCURE input,
    # replacing a previously hardcoded 1.0 that made the schedule fields
    # have zero effect on the calculated sensible/latent gains (audit
    # finding for GC-COOLING-10: "les apports ne reflètent pas toujours
    # les données affichées"). Deliberately does NOT also factor in
    # active_days_count/7: equipment's operating_fraction has no weekly
    # variation concept either, so folding one in here only for occupancy
    # would apply a stricter/different simplification level to one load
    # component than the others feeding the same steady-state calculation.
    occupancy_fraction = fields.Float(compute="_compute_schedule", store=True)
    used_at_night = fields.Boolean(default=False)
    sensible_gain_per_person_w = fields.Float(default=75.0)
    latent_gain_per_person_g_h = fields.Float(default=60.0)
    lighting_power_density_wm2 = fields.Float(default=6.0, help="Installed lighting power per m² of floor area.")
    lighting_usage_fraction = fields.Float(default=0.6, help="Fraction of the day the lighting is actually switched on.")
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

    @api.depends("start_hour", "end_hour", *WEEKDAY_FIELDS)
    def _compute_schedule(self):
        for line in self:
            crosses = line.end_hour < line.start_hour
            if line.end_hour == line.start_hour:
                # A zero-width window is a legitimate "unoccupied" profile
                # (e.g. a technical/server room, README's "local technique
                # sans occupant permanent"), not a midnight crossing.
                hours = 0.0
            elif crosses:
                hours = (24.0 - line.start_hour) + line.end_hour
            else:
                hours = line.end_hour - line.start_hour
            line.crosses_midnight = crosses
            line.daily_occupied_hours = hours
            line.occupancy_fraction = max(0.0, min(1.0, hours / 24.0))
            line.active_days_count = sum(1 for f in WEEKDAY_FIELDS if line[f])

    @api.constrains("usual_occupants", "maximum_occupants")
    def _check_occupants(self):
        for line in self:
            if line.usual_occupants < 0 or line.maximum_occupants < 0:
                raise ValidationError("Occupant counts must not be negative.")
            if line.maximum_occupants < line.usual_occupants:
                raise ValidationError("Maximum occupants must be >= usual occupants.")
            if line.usual_occupants > 500:
                raise ValidationError("Usual occupants must not exceed 500.")
            if line.maximum_occupants > 1000:
                raise ValidationError("Maximum occupants must not exceed 1000.")

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

    @api.constrains("usual_occupants", *WEEKDAY_FIELDS)
    def _check_at_least_one_active_day(self):
        # README §"Validation du planning": "au moins une période si l'usage
        # est occupé". A profile with occupants but zero active weekdays
        # would silently produce a schedule the solver can never place.
        for line in self:
            if line.usual_occupants > 0 and not any(line[f] for f in WEEKDAY_FIELDS):
                raise ValidationError(
                    "At least one weekday must be active when the profile has occupants."
                )

    def write(self, vals):
        # Mirrors greencube.cooling.study.LOCKED_STATES: a validated study
        # is a frozen commercial/technical record end-to-end, not just at
        # the study header (audit gap for GC-COOLING-10 -- the study's own
        # write() guard never covered occupancy_profile_ids, so occupancy
        # could still be edited directly on a validated study with no
        # revision). `provenance` alone stays writable so
        # action_confirm_assumptions() keeps working after validation
        # (bulk-confirming an assumption is not a data change).
        for line in self:
            if line.study_id.state == "validated" and set(vals.keys()) - {"provenance"}:
                raise UserError(
                    "This study is validated and locked. Create a revision to change its occupancy data."
                )
        return super().write(vals)

    def unlink(self):
        if any(line.study_id.state == "validated" for line in self):
            raise UserError(
                "Occupancy data of a validated study cannot be deleted directly; create a revision instead."
            )
        return super().unlink()
