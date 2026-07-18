# -*- coding: utf-8 -*-
"""Geolocation service for GC-COOLING-03: address search, altitude and
timezone resolution, backed by the free Open-Meteo APIs (no API key
required). Pure functions, independent of the ORM except for the optional
cache lookup passed in by the caller — mirrors the MERCURE/compatibility
services' "logic outside the ORM" style used elsewhere in this module.
"""
import logging

import requests

_logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_S = 6


class GeoServiceError(Exception):
    """Raised when the upstream geolocation provider cannot be reached or
    returns an unusable response. Callers should degrade gracefully (keep
    manual lat/lon entry) rather than block the user on a network hiccup."""


def search_address(query, limit=5, language="fr"):
    """Return up to `limit` candidate places for a free-text address/place query."""
    if not query or not query.strip():
        return []
    try:
        response = requests.get(
            GEOCODING_URL,
            params={"name": query.strip(), "count": limit, "language": language, "format": "json"},
            timeout=TIMEOUT_S,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise GeoServiceError(f"Geocoding provider unreachable: {exc}") from exc

    results = []
    for item in data.get("results", []) or []:
        label_parts = [item.get("name")]
        admin = item.get("admin1")
        country = item.get("country")
        if admin and admin != item.get("name"):
            label_parts.append(admin)
        if country:
            label_parts.append(country)
        results.append(
            {
                "label": ", ".join(p for p in label_parts if p),
                "city": item.get("name"),
                "zip": item.get("postcodes", [None])[0] if item.get("postcodes") else None,
                "country_code": item.get("country_code"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "altitude_m": item.get("elevation"),
                "timezone": item.get("timezone"),
            }
        )
    return results


def get_geo_context(latitude, longitude):
    """Resolve altitude (m) and IANA timezone for a given coordinate pair.

    Open-Meteo's forecast endpoint returns both elevation and timezone in a
    single call when timezone=auto is requested, so one request covers both
    pieces of GC-COOLING-03 instead of two.
    """
    try:
        response = requests.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current_weather": "true",
                "timezone": "auto",
            },
            timeout=TIMEOUT_S,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise GeoServiceError(f"Geo-context provider unreachable: {exc}") from exc

    return {
        "altitude_m": data.get("elevation"),
        "timezone": data.get("timezone"),
        "utc_offset_seconds": data.get("utc_offset_seconds"),
    }
