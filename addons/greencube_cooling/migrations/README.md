# Migration policy — greencube_cooling

Required by GC-COOLING-01 §10 ("toute modification de schéma doit disposer
d'une stratégie de migration"). This module had accumulated several
sessions of additive schema changes (new models, new fields) without ever
bumping `version` in `__manifest__.py` or creating this directory — that
gap is what this fixes.

## When a migration script is actually needed here

Odoo's ORM auto-creates new tables and new columns on `-u` upgrade
(`_auto_init`), so most additive changes in this module's history need
**no script**:
- Brand-new models (`calculation.snapshot`, `calculation.job`,
  `simulation.artifact`, `geo.cache`, `climate.dataset`, ...): Odoo creates
  the table; there is no prior data to reconcile.
- New optional fields with a default that is equally valid for old and new
  rows (e.g. a new `Char`/`Boolean` field defaulting to `False`/`""`):
  the ORM's own backfill is correct.

A script **is** needed when a new field's default is only correct for
*new* rows and would silently change the meaning of *existing* rows if
left at that default — see `18.0.2.0.0/post-migrate.py` for a concrete
case: `maximum_acceptable_temperature_c` replaced an inline
`cooling_setpoint_c + 2` computation, so pre-existing studies must be
backfilled with that same formula, not the new field's flat default.

The same rule applies to any future field/column rename (`pre-migrate.py`,
since the old column must still exist to copy from) or any change that
alters the *meaning* of previously-stored values.

## Bumping the version

Every session that changes `models/*.py` in a way covered by the rule
above must:
1. Bump `version` in `__manifest__.py` (the third digit, `18.0.X.0.0`, for
   additive/data-migrating changes; the fourth for pure bugfixes with no
   schema impact).
2. Add `migrations/<new-version>/{pre,post}-migrate.py` if — and only if —
   the rule above applies.

## What has never been verified

Like the rest of this module (see `docs/cooling_v2_traceability_matrix.md`),
no migration script here has been executed against a real Odoo instance
with pre-existing data. `18.0.2.0.0/post-migrate.py` was reviewed by
reading and by `ast.parse`, not by running an actual `-u` upgrade.
