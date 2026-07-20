# -*- coding: utf-8 -*-
"""
Backfill for greencube.cooling.study.maximum_acceptable_temperature_c.

Before this version, the MERCURE input builder computed the maximum
acceptable comfort temperature on the fly as `cooling_setpoint_c + 2`
(see models/cooling_study.py, _build_mercure_input) — there was no stored
field and no way for the user to set it. This version adds a real
`maximum_acceptable_temperature_c` field with a static default (25.0) so it
can be edited like any other field.

A static default is correct for *new* studies, but wrong for studies that
already existed before the upgrade: their calculations were governed by
their own `cooling_setpoint_c + 2`, not by a flat 25.0. Without this
backfill, upgrading would silently change the effective comfort ceiling of
every pre-existing study — exactly the kind of undocumented schema-change
side effect GC-COOLING-01 requires a migration to prevent.

Idempotent: safe to run more than once, and safe even if Odoo's own
auto_init already populated the column with the static default, since we
unconditionally recompute it from cooling_setpoint_c rather than only
filling NULLs.
"""

import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        # Fresh install, not an upgrade from an older version — nothing to
        # backfill, new rows already get the correct value via ORM defaults
        # going forward.
        return

    cr.execute(
        """
        UPDATE greencube_cooling_study
        SET maximum_acceptable_temperature_c = cooling_setpoint_c + 2
        WHERE maximum_acceptable_temperature_c IS NULL
           OR maximum_acceptable_temperature_c != cooling_setpoint_c + 2
        """
    )
    logger.info(
        "greencube_cooling 18.0.2.0.0 post-migrate: backfilled maximum_acceptable_temperature_c "
        "for %s existing greencube.cooling.study row(s).",
        cr.rowcount,
    )
