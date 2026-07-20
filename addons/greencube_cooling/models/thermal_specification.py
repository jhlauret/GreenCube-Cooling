# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class GreencubeThermalSpecification(models.Model):
    _name = "greencube.thermal.specification"
    _description = "GreenCube Thermal Specification"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, version desc"
    _sql_constraints = [
        (
            "code_version_company_uniq",
            "unique(code, version, company_id)",
            "A specification code/version must be unique per company.",
        ),
        ("length_positive", "CHECK(length_m > 0)", "Length must be positive."),
        ("width_positive", "CHECK(width_m > 0)", "Width must be positive."),
        ("height_positive", "CHECK(height_m > 0)", "Height must be positive."),
        ("wall_u_positive", "CHECK(wall_u_value > 0)", "Wall U-value must be positive."),
        ("roof_u_positive", "CHECK(roof_u_value > 0)", "Roof U-value must be positive."),
        ("floor_u_positive", "CHECK(floor_u_value > 0)", "Floor U-value must be positive."),
    ]

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, index=True, tracking=True)
    active = fields.Boolean(default=True)
    version = fields.Char(required=True, tracking=True, default="1.0")

    product_template_id = fields.Many2one("product.template", ondelete="restrict", index=True)
    standard_model = fields.Boolean(default=True)

    source_template_id = fields.Many2one(
        "greencube.thermal.specification",
        ondelete="set null",
        index=True,
        help="Canonical catalog template (standard_model=True) this private specification "
        "was forked from, if any. Kept even if the source template is later archived or "
        "changes version, so provenance stays accurate for historical studies.",
    )
    source_template_version = fields.Char(help="Version of source_template_id at fork time.")

    length_m = fields.Float(required=True, digits=(12, 3))
    width_m = fields.Float(required=True, digits=(12, 3))
    height_m = fields.Float(required=True, digits=(12, 3))

    floor_area_m2 = fields.Float(compute="_compute_geometry", store=True, digits=(12, 3))
    internal_volume_m3 = fields.Float(compute="_compute_geometry", store=True, digits=(12, 3))

    wall_u_value = fields.Float(required=True, digits=(12, 4))
    roof_u_value = fields.Float(required=True, digits=(12, 4))
    floor_u_value = fields.Float(required=True, digits=(12, 4))
    airtightness_n50 = fields.Float(digits=(12, 3))

    thermal_mass_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], required=True, default="medium"
    )
    thermal_bridge_factor = fields.Float(default=0.05, digits=(12, 4))
    default_infiltration_ach = fields.Float(default=0.5, digits=(12, 3))

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    notes = fields.Html()

    facade_ids = fields.One2many("greencube.thermal.facade", "thermal_specification_id")
    study_ids = fields.One2many("greencube.cooling.study", "thermal_specification_id")
    study_count = fields.Integer(compute="_compute_study_count")
    is_locked = fields.Boolean(compute="_compute_is_locked", help="Used in at least one validated study.")

    @api.depends("length_m", "width_m", "height_m")
    def _compute_geometry(self):
        for spec in self:
            spec.floor_area_m2 = spec.length_m * spec.width_m
            spec.internal_volume_m3 = spec.floor_area_m2 * spec.height_m

    def _compute_study_count(self):
        for spec in self:
            spec.study_count = len(spec.study_ids)

    def action_view_studies(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Études",
            "res_model": "greencube.cooling.study",
            "view_mode": "list,form",
            "domain": [("thermal_specification_id", "=", self.id)],
            "context": {"default_thermal_specification_id": self.id},
        }

    def _compute_is_locked(self):
        for spec in self:
            spec.is_locked = bool(spec.study_ids.filtered(lambda s: s.state in ("validated", "calculated")))

    @api.constrains("thermal_bridge_factor")
    def _check_thermal_bridge_factor(self):
        for spec in self:
            if not (0 <= spec.thermal_bridge_factor <= 1):
                raise ValidationError("thermal_bridge_factor must be between 0 and 1.")

    @api.constrains("default_infiltration_ach")
    def _check_infiltration(self):
        for spec in self:
            if spec.default_infiltration_ach < 0:
                raise ValidationError("default_infiltration_ach must be >= 0.")

    LOCKED_FIELDS = (
        "length_m",
        "width_m",
        "height_m",
        "wall_u_value",
        "roof_u_value",
        "floor_u_value",
        "airtightness_n50",
        "thermal_mass_level",
        "thermal_bridge_factor",
        "default_infiltration_ach",
        "facade_ids",
    )

    def write(self, vals):
        for spec in self:
            if spec.is_locked and any(f in vals for f in self.LOCKED_FIELDS):
                raise UserError(
                    "This specification is used by a validated study and its calculatory fields are locked. "
                    "Create a new version instead."
                )
        return super().write(vals)

    def action_create_new_version(self):
        self.ensure_one()
        try:
            major, minor = self.version.split(".")
            next_version = f"{major}.{int(minor) + 1}"
        except ValueError:
            next_version = f"{self.version}-2"
        copy = self.copy({"version": next_version, "name": self.name})
        return {
            "type": "ir.actions.act_window",
            "res_model": "greencube.thermal.specification",
            "res_id": copy.id,
            "view_mode": "form",
            "target": "current",
        }


class GreencubeThermalFacade(models.Model):
    _name = "greencube.thermal.facade"
    _description = "GreenCube Thermal Facade"
    _order = "sequence, id"
    _sql_constraints = [
        (
            "spec_orientation_uniq",
            "unique(thermal_specification_id, orientation)",
            "Only one facade definition per orientation and specification.",
        ),
    ]

    thermal_specification_id = fields.Many2one(
        "greencube.thermal.specification", required=True, ondelete="cascade", index=True
    )
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
    gross_area_m2 = fields.Float(required=True, digits=(12, 3))
    opaque_area_m2 = fields.Float(compute="_compute_areas", store=True, digits=(12, 3))
    glazing_area_m2 = fields.Float(default=0, digits=(12, 3))
    window_u_value = fields.Float(digits=(12, 4))
    solar_factor_g = fields.Float(digits=(12, 4))
    visible_transmittance = fields.Float(digits=(12, 4))
    default_shading_type = fields.Selection(
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
    default_shading_factor = fields.Float(default=1.0, digits=(12, 4))
    facade_code = fields.Char()
    sequence = fields.Integer(default=10)

    @api.depends("gross_area_m2", "glazing_area_m2")
    def _compute_areas(self):
        for facade in self:
            facade.opaque_area_m2 = facade.gross_area_m2 - facade.glazing_area_m2

    @api.constrains("gross_area_m2", "glazing_area_m2")
    def _check_areas(self):
        for facade in self:
            if facade.gross_area_m2 < 0 or facade.glazing_area_m2 < 0:
                raise ValidationError("Areas must not be negative.")
            if facade.glazing_area_m2 > facade.gross_area_m2:
                raise ValidationError("Glazing area cannot exceed the facade's gross area.")

    @api.constrains("solar_factor_g", "visible_transmittance", "default_shading_factor")
    def _check_factors(self):
        for facade in self:
            for value, label in (
                (facade.solar_factor_g, "solar_factor_g"),
                (facade.visible_transmittance, "visible_transmittance"),
                (facade.default_shading_factor, "default_shading_factor"),
            ):
                if value and not (0 <= value <= 1):
                    raise ValidationError(f"{label} must be between 0 and 1.")
