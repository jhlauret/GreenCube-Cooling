from . import models
from . import controllers


def post_init_hook(env):
    """Provisions the MERCURE solver version and GreenCube catalog templates
    for every company that already existed before this module was
    installed — data/solver_version_data.xml and
    data/thermal_specification_catalog_data.xml only ever create rows for
    the company active at install time, so any other pre-existing company
    would otherwise never be able to run a calculation. Idempotent."""
    companies = env["res.company"].search([])
    env["greencube.cooling.solver.version"]._provision_for_companies(companies)
    env["greencube.thermal.specification"]._provision_catalog_for_companies(companies)
