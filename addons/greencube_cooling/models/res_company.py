# -*- coding: utf-8 -*-
from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        # Real gap found by testing a non-superuser user of a second
        # company: greencube.cooling.solver.version and
        # greencube.thermal.specification (standard_model catalog) are both
        # company_id required=True, and their data files only ever create
        # rows for the company active at module install time. Without this,
        # a company created after install could never run a calculation
        # (SOLVER_VERSION_MISSING) nor see any GreenCube model template.
        self.env["greencube.cooling.solver.version"].sudo()._provision_for_companies(companies)
        self.env["greencube.thermal.specification"].sudo()._provision_catalog_for_companies(companies)
        return companies
