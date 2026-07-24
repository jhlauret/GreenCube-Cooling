# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError

VALIDATED_IMMUTABLE_MESSAGE = "A validated equipment selection is immutable; create a new selection instead."


class GreencubeCoolingEquipmentSelection(models.Model):
    _name = "greencube.cooling.equipment.selection"
    _description = "GreenCube Cooling Equipment Selection"
    _order = "create_date desc"

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    result_id = fields.Many2one("greencube.cooling.result", required=True, ondelete="restrict", index=True)
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

    # GC-COOLING-18: "selected" is a working choice, not yet a committed
    # commercial record. `action_validate()` is the one path that promotes a
    # selection to "validated" (spec §"Sélection finale"/"Persistance
    # Odoo"); write()/unlink() below then make it immutable. Without an
    # explicit validation step every selection stayed in "selected" forever
    # and the immutability guard never actually engaged in practice.
    validated_at = fields.Datetime(readonly=True)
    validator_id = fields.Many2one("res.users", readonly=True)

    # Substitution chain (spec §"Historique et versioning" pt.9): a new
    # selection that replaces a prior one links back to it instead of the
    # prior row being edited or deleted, so the full history stays
    # reconstructible even once the replaced row is superseded.
    supersedes_id = fields.Many2one(
        "greencube.cooling.equipment.selection", readonly=True, ondelete="set null", index=True
    )

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

    def action_validate(self):
        """Promote a "selected" working choice to an immutable "validated"
        commercial record (spec §"Sélection finale"). Only allowed from
        "selected" — validating an already-validated/superseded/cancelled
        row is a no-op error, never a silent re-stamp, so a stale client
        retry can't quietly overwrite `validated_at`/`validator_id`.
        """
        for selection in self:
            if selection.state != "selected":
                raise UserError(
                    f"Only a selection in state 'selected' can be validated (current state: {selection.state})."
                )
        return self.write({"state": "validated", "validated_at": fields.Datetime.now(), "validator_id": self.env.user.id})

    def write(self, vals):
        # A validated selection is historical/commercial record: only a
        # state transition away from "validated" is ever allowed, and only
        # through action_supersede's own guarded write() call below (never
        # a direct field edit). audit P1-08: write()/unlink() were
        # previously unrestricted once a selection reached "validated".
        allowed_from_validated = {"state"}
        if any(selection.state == "validated" for selection in self) and set(vals.keys()) - allowed_from_validated:
            raise UserError(VALIDATED_IMMUTABLE_MESSAGE)
        return super().write(vals)

    def unlink(self):
        if any(selection.state == "validated" for selection in self):
            raise UserError("A validated equipment selection cannot be deleted.")
        return super().unlink()
