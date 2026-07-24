# -*- coding: utf-8 -*-
"""
Provisions the MERCURE solver version and GreenCube catalog templates for
every company that already existed in this database before 18.0.4.0.0.

greencube.cooling.solver.version and greencube.thermal.specification
(standard_model rows) are both company_id required=True, and their data
files only ever created rows for the company active when the module was
first installed. An instance upgrading from an older version — with
pre-existing companies beyond that one — would otherwise have those
companies permanently unable to run a calculation (SOLVER_VERSION_MISSING)
or see any GreenCube model template, exactly like a company created after
install would without models/res_company.py's create() override.

Uses the same idempotent provisioning methods post_init_hook and
res.company.create() use, so this is safe to run more than once.
"""
import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    env["greencube.cooling.solver.version"]._provision_for_companies(companies)
    env["greencube.thermal.specification"]._provision_catalog_for_companies(companies)
    logger.info(
        "greencube_cooling 18.0.4.0.0 post-migrate: provisioned solver version + catalog templates "
        "for %s existing compan(y/ies).",
        len(companies),
    )
