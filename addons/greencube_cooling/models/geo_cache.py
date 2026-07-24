# -*- coding: utf-8 -*-
import json
import logging
import time

from odoo import fields, models

from ..services import geo as geo_service

_logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL_DAYS = 90  # README_GC-COOLING-03 §6 "cache TTL : 90 jours"
GEOLOCATION_SCHEMA_VERSION = "1"  # bump if the cached payload shape changes incompatibly


class GreencubeCoolingGeoCache(models.Model):
    _name = "greencube.cooling.geo.cache"
    _description = "GreenCube Cooling Geo Lookup Cache (GC-COOLING-03)"

    cache_key = fields.Char(required=True, index=True)
    kind = fields.Selection([("search", "Address search"), ("context", "Geo context")], required=True)
    payload_json = fields.Text(required=True)
    fetched_epoch = fields.Float(required=True)
    provider = fields.Char(default="open-meteo")
    status = fields.Selection(
        [
            ("available", "Available"),
            ("partial", "Partial"),
            ("stale", "Stale (served past TTL after a provider failure)"),
            ("failed", "Failed"),
        ],
        default="available",
        required=True,
    )
    error_code = fields.Char()
    error_message = fields.Char()

    _sql_constraints = [
        ("cache_key_uniq", "unique(cache_key)", "A geo cache entry already exists for this key."),
    ]

    def _ttl_seconds(self):
        days = self.env["ir.config_parameter"].sudo().get_param(
            "greencube_cooling.geocoding_cache_ttl_days", DEFAULT_CACHE_TTL_DAYS
        )
        try:
            days = float(days)
        except (TypeError, ValueError):
            days = DEFAULT_CACHE_TTL_DAYS
        return days * 24 * 3600

    def _rounded_coord_key(self, kind, latitude, longitude):
        # Rounded to 5 decimals (~1.1 m) per README §8 "Coordonnées:
        # arrondir à cinq décimales" — 3 decimals (~110 m) was too coarse
        # for e.g. two addresses on the same short street to be told apart.
        return f"{kind}:{round(latitude, 5)}:{round(longitude, 5)}:v{GEOLOCATION_SCHEMA_VERSION}"

    def get_or_fetch_context(self, latitude, longitude):
        """Return {altitude_m, timezone, utc_offset_seconds}, using a cached
        entry younger than the configured TTL when available, falling back
        to a live Open-Meteo call otherwise.

        Degradation order (README §5.4 "fournisseur principal -> ... ->
        cache ancien -> résultat partiel"): live provider first; if the
        provider is unreachable, an expired-but-present cache entry is
        served back marked `stale` rather than failing the whole request —
        never inventing a value that was never actually resolved.
        """
        key = self._rounded_coord_key("context", latitude, longitude)
        cached = self.sudo().search([("cache_key", "=", key)], limit=1)
        now = time.time()
        if cached and cached.status in ("available", "stale") and (now - cached.fetched_epoch) < self._ttl_seconds():
            cached.status = "available"
            return json.loads(cached.payload_json)

        try:
            result = geo_service.get_geo_context(latitude, longitude)
        except geo_service.GeoServiceError:
            if cached and cached.payload_json:
                # Fallback tier: an expired-but-present entry beats a hard
                # failure, as long as we are honest that it is stale.
                _logger.warning(
                    "greencube_cooling.geo_cache: provider unreachable, serving stale cache entry "
                    "(kind=context, age_s=%.0f)", now - cached.fetched_epoch,
                )
                cached.write({"status": "stale"})
                return json.loads(cached.payload_json)
            raise

        payload = json.dumps(result)
        is_partial = result.get("altitude_m") is None or result.get("timezone") is None
        status = "partial" if is_partial else "available"
        if cached:
            cached.write(
                {"payload_json": payload, "fetched_epoch": now, "status": status, "error_code": False, "error_message": False}
            )
        else:
            self.sudo().create(
                {
                    "cache_key": key,
                    "kind": "context",
                    "payload_json": payload,
                    "fetched_epoch": now,
                    "status": status,
                }
            )
        return result

    def search_address(self, query, limit=5):
        """Address search results change over time (new places indexed) so
        these are not cached beyond Open-Meteo's own layer; this wrapper only
        exists to keep the controller free of direct HTTP-service imports."""
        return geo_service.search_address(query, limit=limit)
