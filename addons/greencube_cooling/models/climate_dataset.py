# -*- coding: utf-8 -*-
import hashlib
import json
import time
from datetime import datetime

from odoo import fields, models

from ..services import climate as climate_service

CACHE_TTL_SECONDS = 90 * 24 * 3600  # 90 days: historical percentiles barely move faster than that


class GreencubeCoolingClimateDataset(models.Model):
    _name = "greencube.cooling.climate.dataset"
    _description = "GreenCube Cooling Historical Climate Dataset Cache (GC-COOLING-04)"
    _order = "fetched_epoch desc, id desc"

    cache_key = fields.Char(required=True, index=True)
    latitude = fields.Float(digits=(10, 6))
    longitude = fields.Float(digits=(10, 6))
    payload_json = fields.Text(required=True)
    sample_days = fields.Integer()
    data_start = fields.Date()
    data_end = fields.Date()
    fetched_epoch = fields.Float(required=True)
    fetched_at = fields.Datetime(
        string="Fetched at (UTC)",
        help="Same instant as fetched_epoch, in a human-readable Odoo Datetime for display/audit.",
    )

    # --- Provenance / governance (GC-COOLING-04) ---------------------------
    # README §"Modèles Odoo" / §"Immuabilité et versionnement": every stored
    # dataset must state its type, provider, version and schema, and a
    # provider/version/schema change must always produce a *new* dataset
    # row, never a silent reinterpretation of an old one.
    dataset_type = fields.Selection(
        [
            ("historical_observed", "Historique observé"),
            ("typical_year", "Année type"),
            ("design_day", "Jour de dimensionnement"),
            ("extreme_event", "Événement extrême"),
            ("projection", "Projection"),
        ],
        required=True,
        default="historical_observed",
        help=(
            "This service only ever derives scenarios from observed ERA5 "
            "reanalysis history, so 'projection' is reserved for a future "
            "prospective-model provider and is never produced today."
        ),
    )
    provider_code = fields.Char(default=climate_service.PROVIDER_CODE)
    provider_version = fields.Char(default=climate_service.PROVIDER_VERSION)
    schema_version = fields.Integer(default=climate_service.SCHEMA_VERSION)
    license = fields.Char()
    timezone = fields.Char()
    variables = fields.Char(help="Comma-separated provider variable codes actually requested.")
    checksum = fields.Char(
        index=True,
        readonly=True,
        help="SHA-256 of payload_json, computed once at creation. Lets two datasets be compared for "
        "reproducibility without re-fetching, and lets a snapshot record which exact payload it used.",
    )

    # --- Immutability / supersession ----------------------------------------
    # A dataset is never mutated once created: a stale cache entry is
    # archived (active=False, superseded_by_id set) and a brand-new row is
    # created for the refreshed data. This keeps every dataset ever handed
    # to a snapshot/calculation permanently intact and inspectable, even
    # after the location's cache has since refreshed many times over.
    active = fields.Boolean(default=True, index=True)
    superseded_by_id = fields.Many2one("greencube.cooling.climate.dataset", readonly=True, ondelete="set null")

    # Note: no unique SQL constraint on cache_key. Only one *active* row may
    # exist per cache key at a time (enforced in Python by _fetch_active()
    # always filtering active=True); superseded rows deliberately keep the
    # same cache_key so history stays queryable, which a plain
    # unique(cache_key) constraint could not express (Odoo's declarative
    # _sql_constraints cannot express a WHERE-active-only unique index
    # portably).

    def _cache_key(self, latitude, longitude, environment_type):
        return (
            f"{round(latitude, 2)}:{round(longitude, 2)}:{environment_type or 'default'}:"
            f"{climate_service.PROVIDER_CODE}:{climate_service.PROVIDER_VERSION}:{climate_service.SCHEMA_VERSION}"
        )

    @staticmethod
    def _compute_checksum(payload_json):
        return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    def _fetch_active(self, key):
        return self.sudo().search([("cache_key", "=", key), ("active", "=", True)], limit=1)

    def get_or_fetch_scenarios(self, latitude, longitude, environment_type=None):
        """Return the cached historical-scenario payload for this location,
        refetching from Open-Meteo when the cache is stale, missing, or was
        produced by a different provider/version/schema (the cache key
        already embeds those, so a version bump alone is enough to force a
        fresh dataset instead of misreading an old one under a new meaning).

        Never mutates a previously-returned dataset row in place: a stale
        entry is archived (active=False, superseded_by_id) and a new row is
        created, so any dataset id already embedded in a frozen snapshot or
        a `greencube.cooling.climate.scenario` record stays byte-for-byte
        exactly what it was when it was used.
        """
        key = self._cache_key(latitude, longitude, environment_type)
        cached = self._fetch_active(key)
        now = time.time()
        if cached and (now - cached.fetched_epoch) < CACHE_TTL_SECONDS:
            payload = json.loads(cached.payload_json)
            payload["dataset_id"] = cached.id
            payload["dataset_type"] = cached.dataset_type
            payload["checksum"] = cached.checksum
            return payload

        result = climate_service.build_climate_scenarios(latitude, longitude, environment_type)
        payload_json = json.dumps(result)
        checksum = self._compute_checksum(payload_json)
        vals = {
            "cache_key": key,
            "latitude": latitude,
            "longitude": longitude,
            "payload_json": payload_json,
            "sample_days": result["sample_days"],
            "data_start": result["data_start"],
            "data_end": result["data_end"],
            "fetched_epoch": now,
            "fetched_at": datetime.utcfromtimestamp(now),
            "dataset_type": result.get("dataset_type", "historical_observed"),
            "provider_code": result.get("provider_code", climate_service.PROVIDER_CODE),
            "provider_version": result.get("provider_version", climate_service.PROVIDER_VERSION),
            "schema_version": result.get("schema_version", climate_service.SCHEMA_VERSION),
            "license": result.get("license"),
            "timezone": result.get("timezone"),
            "variables": ",".join(result.get("variables", [])),
            "checksum": checksum,
        }
        new_record = self.sudo().create(vals)
        if cached:
            # Archive, never overwrite: the old row (and any dataset_id
            # already referenced from it) remains exactly as it was.
            cached.write({"active": False, "superseded_by_id": new_record.id})

        payload = json.loads(payload_json)
        payload["dataset_id"] = new_record.id
        payload["dataset_type"] = new_record.dataset_type
        payload["checksum"] = checksum
        return payload
