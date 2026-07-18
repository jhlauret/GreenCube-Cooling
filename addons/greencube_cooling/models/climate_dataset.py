# -*- coding: utf-8 -*-
import json
import time

from odoo import fields, models

from ..services import climate as climate_service

CACHE_TTL_SECONDS = 90 * 24 * 3600  # 90 days: historical percentiles barely move faster than that


class GreencubeCoolingClimateDataset(models.Model):
    _name = "greencube.cooling.climate.dataset"
    _description = "GreenCube Cooling Historical Climate Dataset Cache (GC-COOLING-04)"

    cache_key = fields.Char(required=True, index=True)
    latitude = fields.Float(digits=(10, 6))
    longitude = fields.Float(digits=(10, 6))
    payload_json = fields.Text(required=True)
    sample_days = fields.Integer()
    data_start = fields.Date()
    data_end = fields.Date()
    fetched_epoch = fields.Float(required=True)

    _sql_constraints = [
        ("cache_key_uniq", "unique(cache_key)", "A climate dataset cache entry already exists for this key."),
    ]

    def _cache_key(self, latitude, longitude, environment_type):
        return f"{round(latitude, 2)}:{round(longitude, 2)}:{environment_type or 'default'}"

    def get_or_fetch_scenarios(self, latitude, longitude, environment_type=None):
        """Return the cached historical-scenario payload for this location,
        refetching from Open-Meteo when the cache is stale or missing."""
        key = self._cache_key(latitude, longitude, environment_type)
        cached = self.sudo().search([("cache_key", "=", key)], limit=1)
        now = time.time()
        if cached and (now - cached.fetched_epoch) < CACHE_TTL_SECONDS:
            return json.loads(cached.payload_json)

        result = climate_service.build_climate_scenarios(latitude, longitude, environment_type)
        payload = json.dumps(result)
        vals = {
            "payload_json": payload,
            "sample_days": result["sample_days"],
            "data_start": result["data_start"],
            "data_end": result["data_end"],
            "fetched_epoch": now,
        }
        if cached:
            cached.write(vals)
        else:
            self.sudo().create({**vals, "cache_key": key, "latitude": latitude, "longitude": longitude})
        return result
