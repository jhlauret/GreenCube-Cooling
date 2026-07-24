# -*- coding: utf-8 -*-
"""CORS preflight fix (GC-COOLING-02).

Odoo's routing map silently adds ``OPTIONS`` to the allowed methods of
*every* http.route, including our auth="user" business routes (see
odoo/addons/base/models/ir_http.py: ``routing_map()``). Because Werkzeug's
matcher prefers a static path rule (e.g. ``/studies``) over our own
generic ``<path:subpath>`` OPTIONS-only catch-all controller method, a
browser's real CORS preflight request for an exact, already-defined path
was matched to the *business* rule (auth="user") instead of to our
catch-all — and since ``ir.http._authenticate`` runs before dispatch, an
unauthenticated OPTIONS preflight was redirected to /web/login instead of
answered with 204.

Odoo's own built-in fix for this is the ``cors=<value>`` routing key:
``ir.http._authenticate`` special-cases it (``http.is_cors_preflight``) to
force ``auth="none"`` for OPTIONS requests on the matched rule. It was
tried here first, but it has an unwanted side effect for our use case:
``Dispatcher.pre_dispatch`` also unconditionally sets
``Access-Control-Allow-Origin: <cors value>`` on *every* request to a
route carrying that key — not just OPTIONS ones — which corrupted the
real, whitelist-computed header our own ``_guarded``/``_cors_headers``
logic (controllers/api.py) sets on normal GET/POST/PUT/PATCH/DELETE
responses (observed as a doubled, comma-joined header value in testing).
Odoo's ``cors`` key assumes one static, always-trusted origin string; we
need a dynamic, per-request whitelist check instead, so we do not use it.

Instead, this override reimplements just the two things we actually need,
scoped strictly to our own API prefix, and never touches any other
module's routes:
1. ``_authenticate``: for an OPTIONS request under our BASE prefix, skip
   auth entirely (a preflight request never carries a valid session/CSRF
   token and must still be answered) — for every other request/path,
   defer to the normal auth pipeline, unchanged.
2. ``_pre_dispatch``: for that same OPTIONS-under-BASE case, answer
   immediately with our own whitelist-aware headers (mirroring
   controllers.api._cors_headers) instead of ever reaching a business
   controller method — for every other request/path, defer to Odoo's
   normal pre_dispatch, unchanged.
"""
import werkzeug.exceptions

from odoo import models
from odoo.http import request

_BASE = "/api/v1/greencube/cooling"


def _is_our_cors_preflight():
    return request.httprequest.method == "OPTIONS" and request.httprequest.path.startswith(_BASE)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        if _is_our_cors_preflight():
            cls._authenticate_explicit("none")
            return
        return super()._authenticate(endpoint)

    @classmethod
    def _pre_dispatch(cls, rule, args):
        if _is_our_cors_preflight():
            # Local import to avoid a load-time cycle between models/ and
            # controllers/ (controllers/api.py imports from models/).
            from ..controllers.api import _cors_headers

            origin = request.httprequest.headers.get("Origin")
            headers = [
                ("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type, If-Match, Idempotency-Key, X-Request-ID"),
            ] + _cors_headers(origin)
            werkzeug.exceptions.abort(request.make_response("", status=204, headers=headers))
        return super()._pre_dispatch(rule, args)
