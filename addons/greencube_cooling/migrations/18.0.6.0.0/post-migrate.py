# -*- coding: utf-8 -*-
"""
Normalizes any legacy `urban_dense` value in
greencube_cooling_study.environment_type to the canonical `dense_urban`
(GC-COOLING-03 audit finding: "le frontend utilise `urban_dense` alors
qu'Odoo attend `dense_urban`"). By the time this migration ships, the
current code on both sides already only ever writes `dense_urban` — this
script exists purely to repair any row written by an older, buggy build of
either side before that alignment, so an instance upgrading from such a
build does not keep a permanently-invalid `environment_type` (Odoo's
Selection widget silently renders an unrecognized stored value as blank,
which would look identical to "never set" in the UI and pass
`_missing_required_sections()`'s truthiness-unrelated `climate_confirmed`
check without ever being fixed).

Raw SQL (not the ORM) is used deliberately: `environment_type` is a
Selection field, and some Odoo versions refuse to `write()` a value that is
not in the field's current selection list, which `urban_dense` no longer
is — going through cr.execute() sidesteps that entirely.
"""
import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        "SELECT count(*) FROM greencube_cooling_study WHERE environment_type = 'urban_dense'"
    )
    (count,) = cr.fetchone()
    if not count:
        logger.info(
            "greencube_cooling 18.0.6.0.0 post-migrate: no legacy 'urban_dense' rows found, nothing to do."
        )
        return

    cr.execute(
        "UPDATE greencube_cooling_study SET environment_type = 'dense_urban' WHERE environment_type = 'urban_dense'"
    )
    logger.info(
        "greencube_cooling 18.0.6.0.0 post-migrate: normalized %s row(s) from 'urban_dense' to 'dense_urban'.",
        count,
    )
