# -*- coding: utf-8 -*-
from odoo import fields, models


class CoolingApiRateLimitHit(models.Model):
    """One row per rate-limited API call, used only to count recent calls in
    a rolling window (README_GC-COOLING-02_API_ODOO.md §14 "Rate limiting").

    Deliberately minimal: no business data is stored here, and no
    cross-user read path is ever exposed through it — the controller only
    ever queries this model pre-filtered by an explicit user_id (and, for
    study-scoped routes, study_id) that ir.rule has already verified
    ownership of before the controller reaches this helper. It is accessed
    exclusively through sudo() in controllers/api.py: that is bookkeeping
    infrastructure for a rolling counter, not a bypass of any business ACL
    (see docs/cooling_security_matrix.md) — sudo() is required here only
    because counting must work across Odoo's multiple worker processes, so
    an in-memory counter would silently under-count.
    """

    _name = "greencube.cooling.api.rate.limit"
    _description = "GreenCube Cooling API rate-limit hit"
    # _log_access stays at its default (True): create_date is what the
    # rolling-window count in controllers/api.py._check_rate_limit() filters
    # on, so it must exist on the model.

    route_key = fields.Char(required=True, index=True)
    user_id = fields.Many2one("res.users", required=True, index=True, ondelete="cascade")
    study_id = fields.Many2one("greencube.cooling.study", index=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", required=True, index=True)
