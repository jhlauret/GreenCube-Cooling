# -*- coding: utf-8 -*-
import json
import time

from odoo import fields, models

from ..services import geo as geo_service

CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 days: altitude/timezone for a coordinate never really changes


class GreencubeCoolingGeoCache(models.Model):
    _name = "greencube.cooling.geo.cache"
    _description = "GreenCube Cooling Geo Lookup Cache (GC-COOLING-03)"

    cache_key = fields.Char(required=True, index=True)
    kind = fields.Selection([("search", "Address search"), ("context", "Geo context")], required=True)
    payload_json = fields.Text(required=True)
    fetched_epoch = fields.Float(required=True)

    _sql_constraints = [
        ("cache_key_uniq", "unique(cache_key)", "A geo cache entry already exists for this key."),
    ]

    def _rounded_coord_key(self, kind, latitude, longitude):
        return f"{kind}:{round(latitude, 3)}:{round(longitude, 3)}"

    def get_or_fetch_context(self, latitude, longitude):
        """Return {altitude_m, timezone, utc_offset_seconds}, using a cached
        entry younger than CACHE_TTL_SECONDS when available, falling back to
        a live Open-Meteo call otherwise."""
        key = self._rounded_coord_key("context", latitude, longitude)
        cached = self.sudo().search([("cache_key", "=", key)], limit=1)
        now = time.time()
        if cached and (now - cached.fetched_epoch) < CACHE_TTL_SECONDS:
            return json.loads(cached.payload_json)

        result = geo_service.get_geo_context(latitude, longitude)
        payload = json.dumps(result)
        if cached:
            cached.write({"payload_json": payload, "fetched_epoch": now})
        else:
            self.sudo().create({"cache_key": key, "kind": "context", "payload_json": payload, "fetched_epoch": now})
        return result

    def search_address(self, query, limit=5):
        """Address search results change over time (new places indexed) so
        these are not cached beyond Open-Meteo's own layer; this wrapper only
        exists to keep the controller free of direct HTTP-service imports."""
        return geo_service.search_address(query, limit=limit)
