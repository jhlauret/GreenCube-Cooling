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

    def action_supersede(self):
        for selection in self:
            if selection.state == "validated":
                raise UserError("A validated selection cannot be superseded directly; create a new revision.")
            selection.state = "superseded"
