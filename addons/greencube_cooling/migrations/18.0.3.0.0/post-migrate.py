# -*- coding: utf-8 -*-
"""
Removes the `cron_process_pending_energyplus_jobs` ir.cron record.

GC-COOLING-15's worker-isolation requirement rules out running the actual
EnergyPlus simulation call in-process (it had direct PostgreSQL access,
same as every other Odoo cron/web worker). That cron is replaced by the
standalone `energyplus_worker/` process, which only talks to Odoo over the
new /energyplus-jobs/claim and /energyplus-jobs/<id>/complete HTTP routes.

The XML record is `noupdate="1"` and its defining file
(data/energyplus_cron_data.xml) was deleted from the manifest in this same
version — Odoo does not delete orphaned noupdate data on its own, so an
instance upgrading from an older version would otherwise keep a stale,
inactive ir.cron record referencing a model method that no longer exists.
Harmless as long as it stays inactive (its own `active=False` default), but
removed here for cleanliness rather than left to rot.
"""
import logging

logger = logging.getLogger(__name__)

XMLID = "greencube_cooling.cron_process_pending_energyplus_jobs"


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        SELECT model, res_id FROM ir_model_data
        WHERE module = 'greencube_cooling' AND name = 'cron_process_pending_energyplus_jobs'
        """
    )
    row = cr.fetchone()
    if not row:
        logger.info("greencube_cooling 18.0.3.0.0 post-migrate: %s not found, nothing to remove.", XMLID)
        return

    model, res_id = row
    if model == "ir.cron":
        cr.execute("DELETE FROM ir_cron WHERE id = %s", (res_id,))
    cr.execute(
        "DELETE FROM ir_model_data WHERE module = 'greencube_cooling' AND name = 'cron_process_pending_energyplus_jobs'"
    )
    logger.info("greencube_cooling 18.0.3.0.0 post-migrate: removed stale %s (ir_cron id=%s).", XMLID, res_id)
