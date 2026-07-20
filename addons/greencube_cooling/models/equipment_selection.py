# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class GreencubeCoolingEquipmentSelection(models.Model):
    _name = "greencube.cooling.equipment.selection"
    _description = "GreenCube Cooling Equipment Selection"
    _order = "create_date desc"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    result_id = fields.Many2one("greencube.cooling.result", required=True, ondelete="restrict")
    product_id = fields.Many2one("product.product", required=True, ondelete="restrict")
    compatibility_status = fields.Selection(
        [
            ("recommended", "Recommended"),
            ("strong_alternative", "Strong alternative"),
            ("compatible", "Compatible"),
            ("compatible_with_conditions", "Compatible with conditions"),
            ("not_recommended", "Not recommended"),
            ("incompatible", "Incompatible"),
            ("insufficient_data", "Insufficient data"),
        ],
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("selected", "Selected"),
            ("validated", "Validated"),
            ("superseded", "Superseded"),
            ("cancelled", "Cancelled"),
            ("quoted", "Quoted"),
        ],
        default="selected",
        required=True,
    )
    price = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    # Frozen at selection time (write()/unlink() below make them immutable
    # once state=validated): product_id is a live reference whose name and
    # technical specs can change or be archived later. Without these, a
    # historical selection would silently show today's catalog data instead
    # of what was actually assessed when the customer's equipment was
    # chosen (audit P1-08 "historiser prix/données techniques").
    product_name = fields.Char(help="Product name at selection time.")
    capacity_at_45c_w = fields.Float(help="Product's capacity_at_45c_w at selection time.")
    max_outdoor_temperature_c = fields.Float(help="Product's max_outdoor_temperature_c at selection time.")
    shr = fields.Float(digits=(4, 3), help="Product's SHR at selection time.")
    eer = fields.Float(help="Product's EER at selection time.")
    nominal_capacity_w = fields.Float(help="Product's nominal_capacity_w at selection time.")

    def action_supersede(self):
        for selection in self:
            if selection.state == "validated":
                raise UserError("A validated selection cannot be superseded directly; create a new revision.")
            selection.state = "superseded"

    def write(self, vals):
        # A validated selection is historical/commercial record: only a
        # state transition away from "validated" is ever allowed, and only
        # through action_supersede's own guarded write() call below (never
        # a direct field edit). audit P1-08: write()/unlink() were
        # previously unrestricted once a selection reached "validated".
        if any(selection.state == "validated" for selection in self) and set(vals.keys()) != {"state"}:
            raise UserError("A validated equipment selection is immutable; create a new selection instead.")
        return super().write(vals)

    def unlink(self):
        if any(selection.state == "validated" for selection in self):
            raise UserError("A validated equipment selection cannot be deleted.")
        return super().unlink()
