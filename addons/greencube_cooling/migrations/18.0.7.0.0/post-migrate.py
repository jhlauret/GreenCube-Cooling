# -*- coding: utf-8 -*-
"""
GC-COOLING-10: `greencube.cooling.occupancy.profile` gains seven new
boolean columns (`active_monday` .. `active_sunday`) that become the
authoritative weekly calendar, replacing the previous free-text
`usage_days` ("Mon-Fri"/"Lun-Ven"/...) as the field the solver and
Honeybee/EnergyPlus mapping actually read.

By the time this script runs, Odoo's own `_auto_init` has already added
the new columns and backfilled every existing row with the field's static
Python default (Monday-Friday active, Saturday/Sunday inactive) — correct
for a brand-new profile, but wrong for any existing row whose `usage_days`
text said something different (e.g. "7/7", "Every day", a weekend-only
shop). This script re-derives the booleans from each row's own
(untouched) `usage_days` text on a best-effort basis, so existing studies
do not silently gain a different occupied-days pattern than what their
`usage_days` string described.

Deliberately raw SQL, not the ORM: this only touches plain (non-computed)
boolean columns, so there is no compute/depends chain to trigger, and raw
SQL avoids re-running this module's constrains (e.g.
`_check_at_least_one_active_day`) against rows that may be mid-migration.

Best-effort limitation (documented, not silently pretended to be exact):
free text that does not match a recognized pattern below is left at the
ORM's own Monday-Friday default rather than guessed at — this is a strict
superset of what the previous, purely-decorative `usage_days` field
actually let a user express (it was never validated or parsed by any
existing code path before this migration), so no *previously meaningful*
data is lost, only unparsed strings fall back to the same default a new
profile would get.
"""
import logging

logger = logging.getLogger(__name__)

ALL_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WEEKDAYS_ONLY = ("monday", "tuesday", "wednesday", "thursday", "friday")

# Recognized legacy strings -> set of active day names. Matched
# case-insensitively after stripping whitespace.
EVERY_DAY_PATTERNS = ("7/7", "7j/7", "every day", "everyday", "daily", "tous les jours")
WEEKDAY_ONLY_PATTERNS = ("mon-fri", "lun-ven", "monday-friday", "lundi-vendredi", "5/7")
WEEKEND_ONLY_PATTERNS = ("sat-sun", "sam-dim", "weekend", "week-end")


def _active_days_for_text(text):
    normalized = (text or "").strip().lower()
    if any(p in normalized for p in EVERY_DAY_PATTERNS):
        return set(ALL_DAYS)
    if any(p in normalized for p in WEEKEND_ONLY_PATTERNS):
        return {"saturday", "sunday"}
    if not normalized or any(p in normalized for p in WEEKDAY_ONLY_PATTERNS):
        return set(WEEKDAYS_ONLY)
    # Unrecognized free text: keep the ORM's own Mon-Fri default rather
    # than guess further (documented limitation above).
    return set(WEEKDAYS_ONLY)


def migrate(cr, version):
    if not version:
        return

    cr.execute("SELECT id, usage_days FROM greencube_cooling_occupancy_profile")
    rows = cr.fetchall()
    if not rows:
        logger.info("greencube_cooling 18.0.7.0.0 post-migrate: no occupancy profile rows found, nothing to do.")
        return

    updated = 0
    for profile_id, usage_days in rows:
        active = _active_days_for_text(usage_days)
        cr.execute(
            """
            UPDATE greencube_cooling_occupancy_profile
            SET active_monday = %s, active_tuesday = %s, active_wednesday = %s,
                active_thursday = %s, active_friday = %s, active_saturday = %s,
                active_sunday = %s, active_days_count = %s
            WHERE id = %s
            """,
            (
                "monday" in active,
                "tuesday" in active,
                "wednesday" in active,
                "thursday" in active,
                "friday" in active,
                "saturday" in active,
                "sunday" in active,
                len(active),
                profile_id,
            ),
        )
        updated += 1

    logger.info(
        "greencube_cooling 18.0.7.0.0 post-migrate: backfilled active_<weekday> booleans for %s occupancy profile row(s) from legacy usage_days text.",
        updated,
    )
