# -*- coding: utf-8 -*-
"""JSON API for GreenCube Cooling, per README_GC-COOLING-02_API_ODOO.md.

Routes are intentionally thin: they validate the request, delegate to the
model layer (which owns all business rules), and serialize the response.
No thermal logic lives here — MERCURE stays independent of the ORM and of
this controller.
"""
import datetime
import functools
import json
import logging
import time
import uuid
import zoneinfo

from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request

from ..models.cooling_study import CoolingIdempotencyConflict
from ..services import api_validation
from ..services import geo as geo_service

BASE = "/api/v1/greencube/cooling"

_logger = logging.getLogger(__name__)

# Methods that mutate state and therefore need the Origin/CSRF-equivalent
# check in _guarded (GC-COOLING-02 §8.1/§11): GET/HEAD never write, so they
# are exempt even from a foreign Origin.
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _request_id():
    # Honor a client-supplied X-Request-ID for end-to-end correlation across
    # frontend logs / proxy logs / Odoo logs (GC-COOLING-02 §6); fall back to
    # a server-generated one when absent or empty.
    supplied = None
    try:
        supplied = request.httprequest.headers.get("X-Request-ID")
    except RuntimeError:
        pass  # no request context (e.g. called outside an HTTP request)
    return supplied.strip() if supplied and supplied.strip() else f"req-{uuid.uuid4()}"


def _origin_allowed(origin):
    """True if `origin` may be trusted for a mutating request. Same-origin
    calls (the normal case when Odoo serves the built frontend itself) are
    always allowed by comparing against the request's own host. Any other
    origin must appear in the `greencube_cooling.allowed_frontend_origins`
    ir.config_parameter (comma-separated, exact scheme+host+port match,
    never a wildcard) — GC-COOLING-02 §8.2/§11."""
    if not origin:
        # No Origin header at all: not a cross-origin browser request (most
        # non-browser clients, and same-site top-level navigations, omit
        # it). Nothing to check against.
        return True
    own = request.httprequest.host_url.rstrip("/")
    if origin.rstrip("/") == own:
        return True
    allowed_raw = request.env["ir.config_parameter"].sudo().get_param(
        "greencube_cooling.allowed_frontend_origins", ""
    )
    allowed = {o.strip().rstrip("/") for o in allowed_raw.split(",") if o.strip()}
    return origin.rstrip("/") in allowed


def _cors_headers(origin):
    """Only ever echoes back the exact, whitelisted Origin — never '*' —
    and only when credentials (the Odoo session cookie) are in play, per
    the non-negotiable "no Access-Control-Allow-Origin: * with credentials"
    rule."""
    if origin and _origin_allowed(origin) and origin.rstrip("/") != request.httprequest.host_url.rstrip("/"):
        return [
            ("Access-Control-Allow-Origin", origin),
            ("Access-Control-Allow-Credentials", "true"),
            ("Vary", "Origin"),
        ]
    return []


def _json_response(payload, status=200):
    origin = None
    try:
        origin = request.httprequest.headers.get("Origin")
    except RuntimeError:
        pass
    return request.make_response(
        json.dumps(payload, default=str),
        status=status,
        headers=[("Content-Type", "application/json")] + _cors_headers(origin),
    )


def _error(code, message, status=400, field=None, section=None, action=None, fields=None):
    payload = {
        "error": {
            "code": code,
            "message": message,
            "field": field,
            "section": section,
            "action": action,
            "request_id": _request_id(),
        }
    }
    if fields:
        # Per-field validation detail (README §4.3) additive to the
        # single-field shape above, which the frontend already consumes
        # (GC-COOLING-06) — kept so existing callers are unaffected.
        payload["error"]["fields"] = fields
    return _json_response(payload, status=status)


def _range_error(vals, limits, section):
    """Runs api_validation.validate_ranges() over `vals` and, if anything
    is out of bounds, returns a ready-to-return 422 VALIDATION_ERROR
    response; otherwise returns None so the caller proceeds."""
    errors = api_validation.validate_ranges(vals, limits)
    if not errors:
        return None
    first_field = next(iter(errors))
    return _error(
        "VALIDATION_ERROR",
        "Certaines données sont invalides.",
        status=422,
        field=first_field,
        section=section,
        fields=errors,
    )


def _company_override_error(body):
    """A frontend must never dictate which company a record belongs to
    (GC-COOLING-02 §11 "Ne jamais faire confiance au company_id envoyé par
    le frontend"). Every route already builds its write-vals from an
    explicit allow-list that omits company_id, so this is a defense-in-
    depth, explicit-error layer, not the only thing preventing it."""
    if isinstance(body, dict) and "company_id" in body:
        return _error(
            "COOLING_COMPANY_OVERRIDE_FORBIDDEN",
            "company_id is derived from the authenticated user and cannot be set from the API.",
            status=403,
            field="company_id",
        )
    return None


def _check_rate_limit(route_key, window_seconds, max_count, study=None):
    """Rolling-window rate limit backed by a small DB table (not an
    in-process counter, since Odoo runs multiple worker processes) —
    GC-COOLING-02 §14. Returns a ready 429 response if the caller is over
    the limit, else records this call and returns None."""
    Hit = request.env["greencube.cooling.api.rate.limit"].sudo()
    since = datetime.datetime.utcnow() - datetime.timedelta(seconds=window_seconds)
    domain = [
        ("route_key", "=", route_key),
        ("user_id", "=", request.env.uid),
        ("create_date", ">=", since),
    ]
    if study is not None:
        domain.append(("study_id", "=", study.id))
    if Hit.search_count(domain) >= max_count:
        return _error(
            "RATE_LIMIT_EXCEEDED",
            f"Too many '{route_key}' requests; please try again shortly.",
            status=429,
        )
    Hit.create(
        {
            "route_key": route_key,
            "user_id": request.env.uid,
            "study_id": study.id if study is not None else False,
            "company_id": request.env.company.id,
        }
    )
    return None


def _guarded(fn):
    """Turns ir.rule ownership violations into the standard JSON error
    envelope instead of Odoo's default HTML/plain error page. Every route
    handler on this controller is wrapped with this, since sub-resources
    (occupancy, equipment, results, ...) are addressed directly by numeric
    id and rely entirely on ir.rule for ownership enforcement (audit
    P0-05).

    Also, per GC-COOLING-02:
    - rejects mutating (POST/PUT/PATCH/DELETE) requests whose Origin header
      is neither this Odoo instance's own origin nor on the configured
      frontend whitelist — this is the actual CSRF-equivalent defense for
      these routes (they run with csrf=False because they use a bearer-less
      session cookie consumed by a same-origin-or-whitelisted SPA rather
      than an HTML form; see docs/cooling_security_matrix.md §"CSRF/CORS
      strategy" for the full rationale);
    - logs one structured line per request (route, method, user, company,
      status, duration) without ever including headers, cookies or body
      content, so secrets/PII never reach the log (§6);
    - maps CoolingIdempotencyConflict to 409 IDEMPOTENCY_CONFLICT and a
      bare ValidationError (e.g. an ORM constraint outside the try/except
      blocks already handling it per-route) to 422 VALIDATION_ERROR,
      instead of letting either fall through to Odoo's default error page.
    """

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        started = time.monotonic()
        method = request.httprequest.method
        route = request.httprequest.path
        status_code = 200
        try:
            if method in _MUTATING_METHODS:
                origin = request.httprequest.headers.get("Origin")
                if origin and not _origin_allowed(origin):
                    status_code = 403
                    return _error(
                        "ACCESS_DENIED",
                        "This origin is not allowed to perform this request.",
                        status=403,
                    )
            return fn(self, *args, **kwargs)
        except CoolingIdempotencyConflict as exc:
            status_code = 409
            return _error("IDEMPOTENCY_CONFLICT", str(exc), status=409, section="results")
        except AccessError as exc:
            status_code = 403
            return _error("COOLING_ACCESS_DENIED", str(exc), status=403)
        except MissingError as exc:
            status_code = 404
            return _error("COOLING_NOT_FOUND", str(exc), status=404)
        except ValidationError as exc:
            status_code = 422
            return _error("VALIDATION_ERROR", str(exc), status=422)
        finally:
            duration_ms = int((time.monotonic() - started) * 1000)
            try:
                uid = request.env.uid
                company_id = request.env.company.id
            except Exception:
                uid = company_id = None
            _logger.info(
                "greencube_cooling.api route=%s method=%s user_id=%s company_id=%s "
                "status_code=%s duration_ms=%s",
                route, method, uid, company_id, status_code, duration_ms,
            )

    return wrapper




def _body():
    try:
        raw = request.httprequest.get_data()
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return None


def _serialize_study(study):
    return {
        "id": study.id,
        "reference": study.reference,
        "name": study.name,
        "state": study.state,
        "revision_number": study.revision_number,
        "parent_study_id": study.parent_study_id.id or None,
        "root_study_id": study.root_study_id.id or None,
        "thermal_specification_id": study.thermal_specification_id.id or None,
        "partner_id": study.partner_id.id or None,
        "company_id": study.company_id.id,
        "location": {
            "address": study.address,
            "city": study.city,
            "zip": study.zip,
            # Not `or None`: Odoo Float fields default to 0.0 for "unset",
            # indistinguishable from a real equator/meridian coordinate, so
            # coercing 0.0 to null would silently hide a valid location.
            # `climate_confirmed` is the actual presence signal (GC-COOLING-03).
            "latitude": study.latitude,
            "longitude": study.longitude,
            "altitude_m": study.altitude_m,
            "timezone": study.timezone or None,
            "environment_type": study.environment_type or None,
            "climate_confirmed": study.climate_confirmed,
            "main_orientation": study.main_orientation or None,
            # Provenance/precision/audit trail (GC-COOLING-03): who/what
            # resolved the values above, and when. Never the raw provider
            # payload — see location_source_json's own docstring.
            "location_provenance": study.location_provenance or None,
            "location_precision": study.location_precision or None,
            "location_provider": study.location_provider or None,
            "location_resolved_at": study.location_resolved_at.isoformat() if study.location_resolved_at else None,
            # Populated only after the first action_calculate()/create_snapshot()
            # run (GC-COOLING-04): the three named scenarios as last computed,
            # each carrying its own provenance/dataset_type/period/checksum so
            # the caller never has to guess whether a value is real historical
            # data or the altitude-based fallback heuristic.
            "climate_scenarios": [_serialize_climate_scenario(s) for s in study.climate_scenario_ids],
        },
        "comfort": {
            "cooling_setpoint_c": study.cooling_setpoint_c,
            "night_setpoint_offset_c": study.night_setpoint_offset_c,
            "maximum_acceptable_temperature_c": study.maximum_acceptable_temperature_c,
            "target_humidity_percent": study.target_humidity_percent,
            "service_level": study.service_level,
        },
        "confidence_score": study.confidence_score,
        "input_snapshot_hash": study.input_snapshot_hash or None,
        "active_result_id": study.active_result_id.id or None,
        "active_snapshot_id": study.active_snapshot_id.id or None,
        "updated_at": study.write_date.isoformat() if study.write_date else None,
    }


def _serialize_climate_scenario(scenario):
    # Exposes provenance/freshness/period so a consumer (GC-COOLING-07's
    # UI, GC-COOLING-13's review screen) can honestly show "historical data
    # from provider X, covering period Y, last computed on Z" instead of
    # the frontend guessing or recomputing this itself (README_GC-COOLING-04
    # "Exposer au frontend la provenance, la période, la fraîcheur et les
    # avertissements" / "éviter tout appel direct aux fournisseurs météo
    # depuis le frontend").
    detail = {}
    if scenario.detail_json:
        try:
            detail = json.loads(scenario.detail_json)
        except json.JSONDecodeError:
            detail = {}
    return {
        "id": scenario.id,
        "scenario_type": scenario.scenario_type,
        "outdoor_temperature_c": scenario.outdoor_temperature_c,
        "relative_humidity_percent": scenario.relative_humidity_percent,
        "solar_radiation_wm2": scenario.solar_radiation_wm2,
        "wind_speed_ms": scenario.wind_speed_ms,
        "provenance": scenario.provenance,
        "dataset_type": scenario.dataset_type or None,
        "checksum": scenario.checksum or None,
        "reference_date": detail.get("reference_date"),
        "data_start": detail.get("data_start"),
        "data_end": detail.get("data_end"),
        "sample_days": detail.get("sample_days"),
        "provider_code": detail.get("provider_code"),
        "provider_version": detail.get("provider_version"),
        "timezone": detail.get("timezone"),
        "license": detail.get("license"),
    }


def _serialize_facade(facade):
    return {
        "id": facade.id,
        "orientation": facade.orientation,
        "gross_area_m2": facade.gross_area_m2,
        "opaque_area_m2": facade.opaque_area_m2,
        "glazing_area_m2": facade.glazing_area_m2,
        "window_u_value": facade.window_u_value,
        "solar_factor_g": facade.solar_factor_g,
        "visible_transmittance": facade.visible_transmittance,
        "default_shading_type": facade.default_shading_type,
        "default_shading_factor": facade.default_shading_factor,
    }


def _serialize_thermal_spec(spec):
    return {
        "id": spec.id,
        "name": spec.name,
        "code": spec.code,
        "version": spec.version,
        "standard_model": spec.standard_model,
        "product_template_id": spec.product_template_id.id or None,
        "source_template_id": spec.source_template_id.id or None,
        "source_template_version": spec.source_template_version or None,
        "length_m": spec.length_m,
        "width_m": spec.width_m,
        "height_m": spec.height_m,
        "floor_area_m2": spec.floor_area_m2,
        "internal_volume_m3": spec.internal_volume_m3,
        "wall_u_value": spec.wall_u_value,
        "roof_u_value": spec.roof_u_value,
        "floor_u_value": spec.floor_u_value,
        "airtightness_n50": spec.airtightness_n50,
        "thermal_mass_level": spec.thermal_mass_level,
        "thermal_bridge_factor": spec.thermal_bridge_factor,
        "default_infiltration_ach": spec.default_infiltration_ach,
        "is_locked": spec.is_locked,
        "facades": [_serialize_facade(f) for f in spec.facade_ids],
    }


def _serialize_occupancy(profile):
    return {
        "id": profile.id,
        "usage_type": profile.usage_type,
        "usual_occupants": profile.usual_occupants,
        "maximum_occupants": profile.maximum_occupants,
        "activity_level": profile.activity_level,
        # Legacy free-text display summary; not authoritative (GC-COOLING-10).
        "usage_days": profile.usage_days,
        "active_monday": profile.active_monday,
        "active_tuesday": profile.active_tuesday,
        "active_wednesday": profile.active_wednesday,
        "active_thursday": profile.active_thursday,
        "active_friday": profile.active_friday,
        "active_saturday": profile.active_saturday,
        "active_sunday": profile.active_sunday,
        "active_days_count": profile.active_days_count,
        "start_hour": profile.start_hour,
        "end_hour": profile.end_hour,
        "crosses_midnight": profile.crosses_midnight,
        "daily_occupied_hours": profile.daily_occupied_hours,
        "occupancy_fraction": profile.occupancy_fraction,
        "used_at_night": profile.used_at_night,
        "sensible_gain_per_person_w": profile.sensible_gain_per_person_w,
        "latent_gain_per_person_g_h": profile.latent_gain_per_person_g_h,
        "lighting_power_density_wm2": profile.lighting_power_density_wm2,
        "lighting_usage_fraction": profile.lighting_usage_fraction,
        "provenance": profile.provenance,
    }


def _serialize_ventilation(profile):
    return {
        "id": profile.id,
        "ventilation_type": profile.ventilation_type,
        "airflow_m3h": profile.airflow_m3h,
        "air_changes_per_hour": profile.air_changes_per_hour,
        "heat_recovery_efficiency_percent": profile.heat_recovery_efficiency_percent,
        "door_opening_frequency": profile.door_opening_frequency,
        "window_opening_frequency": profile.window_opening_frequency,
        "airtightness_n50": profile.airtightness_n50,
        "wind_exposure": profile.wind_exposure,
        "infiltration_ach": profile.infiltration_ach,
        # The value actually used by the solver, per get_effective_infiltration_ach()
        # (n50-derived when set, else infiltration_ach, plus door/window opening
        # increments) — exposed so the UI never has to duplicate that conversion
        # (GC-COOLING-12).
        "effective_infiltration_ach": profile.get_effective_infiltration_ach(),
        "fan_power_w": profile.fan_power_w,
        "fan_fraction_dissipated_in_zone": profile.fan_fraction_dissipated_in_zone,
        "bypass_active": profile.bypass_active,
        "provenance": profile.provenance,
    }


def _serialize_shading(shading):
    return {
        "id": shading.id,
        "orientation": shading.orientation,
        "shading_type": shading.shading_type,
        "efficiency_percent": shading.efficiency_percent,
        "start_hour": shading.start_hour,
        "end_hour": shading.end_hour,
        "automatic": shading.automatic,
        "confirmed": shading.confirmed,
        "provenance": shading.provenance,
    }


def _serialize_equipment_load(line):
    return {
        "id": line.id,
        "product_id": line.product_id.id or None,
        "name": line.name,
        "category": line.category,
        "quantity": line.quantity,
        "unit_power_w": line.unit_power_w,
        "usage_hours_per_day": line.usage_hours_per_day,
        "simultaneity_percent": line.simultaneity_percent,
        "heat_dissipation_factor": line.heat_dissipation_factor,
        "permanent_operation": line.permanent_operation,
        "provenance": line.provenance,
        "notes": line.notes,
        "thermal_load_w": line.thermal_load_w,
    }


def _equipment_load_vals(body):
    return {
        k: body[k]
        for k in (
            "product_id",
            "name",
            "category",
            "quantity",
            "unit_power_w",
            "usage_hours_per_day",
            "simultaneity_percent",
            "heat_dissipation_factor",
            "permanent_operation",
            "provenance",
            "notes",
        )
        if k in body
    }


def _serialize_result(result):
    # The job that produced this result is looked up by result_id rather
    # than stored as a direct field on greencube.cooling.result, so the
    # result record stays a pure, immutable numeric artifact — the job is
    # only ever a many-to-one pointer *to* a result, never the reverse.
    # Frontend needs it anyway (GC-COOLING-16) to know whether an
    # EnergyPlus tail (energyplus_processing_status) is still pending for
    # this specific result, distinct from the result's own numbers, which
    # are already final and immutable by the time this row exists.
    job = result.env["greencube.cooling.calculation.job"].search(
        [("result_id", "=", result.id)], limit=1, order="create_date desc"
    )
    return {
        "id": result.id,
        "study_id": result.study_id.id,
        "job_id": job.id if job else None,
        "engine": "MERCURE",
        "engine_version": result.solver_version_id.version if result.solver_version_id else None,
        "requested_engine": result.snapshot_id.requested_engine if result.snapshot_id else None,
        "energyplus_processing_status": job.energyplus_processing_status if job else "not_requested",
        # A study only ever has one "active" (latest successful) result at
        # a time (see _compute_active_result). Anything else — an older
        # successful run before a revision/recalculation, or a failed one —
        # must never be presented as the study's current recommendation,
        # so the frontend gets this as an explicit flag instead of having
        # to reimplement "latest successful" logic itself (audit: frontend
        # must never guess which result is authoritative).
        "is_current": bool(result.study_id.active_result_id) and result.study_id.active_result_id.id == result.id,
        "state": result.state,
        "governing_scenario_code": result.governing_scenario_code,
        "sensible_load_w": result.sensible_load_w,
        "latent_load_w": result.latent_load_w,
        "total_load_w": result.total_load_w,
        "shr": result.shr,
        "margin_w": result.margin_w,
        "recommended_capacity_w": result.recommended_capacity_w,
        "recommended_capacity_kw": result.recommended_capacity_kw,
        "recommended_capacity_btu_h": result.recommended_capacity_btu_h,
        "commercial_capacity": {
            "id": result.commercial_capacity_id.id,
            "name": result.commercial_capacity_id.name,
            "capacity_btu_h": result.commercial_capacity_id.capacity_btu_h,
            "capacity_kw": result.commercial_capacity_id.capacity_kw,
        } if result.commercial_capacity_id else None,
        "confidence_score": result.confidence_score,
        "warnings": json.loads(result.warnings_json or "[]"),
        "main_load_drivers": json.loads(result.main_load_drivers_json or "[]"),
        # Per-facade decomposition of the "solar_glazing" breakdown entry
        # (GC-COOLING-09 pt.11) — informative only, already included once in
        # `breakdown`'s "solar_glazing" total, never summed on top of it.
        "solar_gain_by_facade": json.loads(result.solar_gain_by_facade_json or "[]"),
        "breakdown": [
            {
                "component_code": c.component_code,
                "label": c.label,
                "sensible_w": c.sensible_w,
                "latent_w": c.latent_w,
                "total_w": c.total_w,
                "percentage_of_total": c.percentage_of_total,
            }
            for c in result.component_ids
        ],
        "duration_ms": result.duration_ms,
        "created_at": result.create_date.isoformat() if result.create_date else None,
    }


def _serialize_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "type": product.cooling_equipment_type,
        "nominal_capacity_w": product.nominal_capacity_w,
        "capacity_at_35c_w": product.capacity_at_35c_w,
        "capacity_at_45c_w": product.capacity_at_45c_w,
        "electrical_power_w": product.electrical_power_w,
        "eer": product.eer,
        "seer": product.seer,
        "shr": product.cooling_shr,
        "noise_db": product.noise_db,
        "max_outdoor_temperature_c": product.max_outdoor_temperature_c,
        "power_supply": product.power_supply,
        "data_quality": product.data_quality,
        "list_price": product.list_price,
    }


def _serialize_internal_load_product(product):
    return {
        "id": product.id,
        "code": product.internal_load_code or None,
        "name": product.name,
        "category": product.internal_load_category,
        "unit_power_w": product.internal_load_unit_power_w,
        "usage_hours_per_day": product.internal_load_usage_hours_per_day,
        "simultaneity_percent": product.internal_load_simultaneity_percent,
        "data_quality": product.data_quality,
    }


def _serialize_equipment_selection(selection):
    return {
        "id": selection.id,
        "product_id": selection.product_id.id,
        # Frozen at selection time, not read live off product_id (audit
        # P1-08) — a renamed/archived/re-specced product must not silently
        # rewrite this selection's history.
        "product_name": selection.product_name,
        "capacity_at_45c_w": selection.capacity_at_45c_w,
        "max_outdoor_temperature_c": selection.max_outdoor_temperature_c,
        "shr": selection.shr,
        "eer": selection.eer,
        "nominal_capacity_w": selection.nominal_capacity_w,
        "price": selection.price,
        "currency": selection.currency_id.name if selection.currency_id else None,
        "compatibility_status": selection.compatibility_status,
        "state": selection.state,
        "result_id": selection.result_id.id,
        "created_at": selection.create_date.isoformat() if selection.create_date else None,
        "validated_at": selection.validated_at.isoformat() if selection.validated_at else None,
        "validator_id": selection.validator_id.id or None,
        "supersedes_id": selection.supersedes_id.id or None,
    }


class GreencubeCoolingApiController(http.Controller):

    # ------------------------------------------------------------------
    # CORS preflight (GC-COOLING-02 §8.2)
    # ------------------------------------------------------------------

    @http.route(
        f"{BASE}/<path:subpath>", type="http", auth="public", methods=["OPTIONS"], csrf=False, save_session=False
    )
    def cors_preflight(self, subpath, **kwargs):
        """Generic CORS preflight responder for every route under BASE.
        Actual authorization/ownership is still enforced on the real
        request by each route's own auth="user" + ir.rule + _guarded's
        Origin check — this endpoint only ever answers the browser's
        preflight OPTIONS, never business data."""
        origin = request.httprequest.headers.get("Origin")
        headers = [
            ("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type, If-Match, Idempotency-Key, X-Request-ID"),
        ] + _cors_headers(origin)
        return request.make_response("", status=204, headers=headers)

    # ------------------------------------------------------------------
    # Studies
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def list_studies(self, limit=None, offset=None, search=None, **kwargs):
        try:
            limit = max(1, min(int(limit), 200)) if limit else 50
            offset = max(0, int(offset)) if offset else 0
        except (TypeError, ValueError):
            return _error("COOLING_INVALID_PAGINATION", "limit/offset must be integers.", status=400, section="studies")
        domain = [("name", "ilike", search)] if search else []
        Study = request.env["greencube.cooling.study"]
        total = Study.search_count(domain)
        studies = Study.search(domain, order="create_date desc", limit=limit, offset=offset)
        return _json_response(
            {
                "data": [_serialize_study(s) for s in studies],
                "meta": {"total": total, "limit": limit, "offset": offset},
            }
        )

    @http.route(f"{BASE}/studies", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def create_study(self, **kwargs):
        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        override_error = _company_override_error(body)
        if override_error:
            return override_error
        name = body.get("name") or "New study"
        study = request.env["greencube.cooling.study"].create({"name": name})
        return _json_response({"data": _serialize_study(study)}, status=201)

    @http.route(f"{BASE}/studies/<int:study_id>", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def get_study(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": _serialize_study(study)})

    @http.route(f"{BASE}/studies/<int:study_id>", type="http", auth="user", methods=["PATCH"], csrf=False)
    @_guarded
    def patch_study(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")

        if_match = request.httprequest.headers.get("If-Match")
        current_version = study.write_date.isoformat() if study.write_date else None
        if if_match and current_version and if_match != current_version:
            return _error(
                "COOLING_STUDY_VERSION_CONFLICT",
                "This study was modified by someone else since it was last read. Reload and retry.",
                status=409,
                section="studies",
            )

        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        override_error = _company_override_error(body)
        if override_error:
            return override_error

        patchable = {
            "name",
            "partner_id",
            "thermal_specification_id",
            "address",
            "city",
            "zip",
            "latitude",
            "longitude",
            "altitude_m",
            "timezone",
            "environment_type",
            "climate_confirmed",
            "main_orientation",
            "cooling_setpoint_c",
            "night_setpoint_offset_c",
            "maximum_acceptable_temperature_c",
            "target_humidity_percent",
            "service_level",
        }
        vals = {k: v for k, v in body.items() if k in patchable}
        range_error = _range_error(vals, api_validation.FIELD_LIMITS, section="location")
        if range_error:
            return range_error
        try:
            study.write(vals)
        except AccessError:
            # See confirm_location()'s identical guard just below: AccessError
            # is itself a UserError subclass, so without this it would be
            # misreported as 409 "study locked" instead of 403 "access
            # denied" for a cross-user/cross-company PATCH attempt (found
            # while adding the GC-COOLING-03 cross-user location test).
            raise
        except (UserError, ValidationError) as exc:
            return _error("COOLING_STUDY_LOCKED", str(exc), status=409, section="studies", action="create_revision")
        if vals:
            study._invalidate_active_snapshot()
        return _json_response({"data": _serialize_study(study)})

    # ------------------------------------------------------------------
    # Geolocation (GC-COOLING-03): address search, altitude, timezone
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/geocode", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def geocode(self, query=None, **kwargs):
        if not query or not query.strip():
            return _error("GEOCODE_QUERY_REQUIRED", "A non-empty 'query' parameter is required.", status=400, field="query")
        limited = _check_rate_limit("geocode", window_seconds=60, max_count=30)
        if limited:
            return limited
        try:
            matches = request.env["greencube.cooling.geo.cache"].search_address(query)
        except geo_service.GeoServiceError as exc:
            return _error("GEO_PROVIDER_UNAVAILABLE", str(exc), status=502, section="location")
        return _json_response({"data": matches})

    @http.route(f"{BASE}/geo-context", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def geo_context(self, latitude=None, longitude=None, **kwargs):
        if latitude is None or longitude is None:
            return _error(
                "GEO_CONTEXT_COORDS_REQUIRED",
                "Both 'latitude' and 'longitude' query parameters are required.",
                status=400,
                field="latitude",
                section="location",
            )
        try:
            lat, lon = float(latitude), float(longitude)
        except ValueError:
            return _error("GEO_CONTEXT_INVALID_COORDS", "latitude/longitude must be numeric.", status=400, section="location")
        range_error = _range_error({"latitude": lat, "longitude": lon}, api_validation.FIELD_LIMITS, section="location")
        if range_error:
            return range_error
        # README §14 specifies 10/hour/study for the climate route; this
        # endpoint is coordinate-scoped rather than study-scoped in this
        # repo's actual implementation (no study_id in the path), so the
        # limit is applied per-user instead — documented deviation, see
        # final report "décisions d'architecture".
        limited = _check_rate_limit("climate", window_seconds=3600, max_count=10)
        if limited:
            return limited
        try:
            context = request.env["greencube.cooling.geo.cache"].get_or_fetch_context(lat, lon)
        except geo_service.GeoServiceError as exc:
            return _error("GEO_PROVIDER_UNAVAILABLE", str(exc), status=502, section="location")
        return _json_response({"data": context})

    @http.route(f"{BASE}/studies/<int:study_id>/confirm-location", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def confirm_location(self, study_id, **kwargs):
        """GC-COOLING-03 §16/§17: the *only* route that is allowed to set
        `climate_confirmed = True`. A plain PATCH /studies/<id> can still
        write raw lat/lon (e.g. a "clear the location" reset), but never
        touches provenance/precision/resolved_at, and the frontend must
        call this route once the user explicitly confirms a location
        before it is "locked in" (README §16 "Une simple recherche ne doit
        pas modifier définitivement l'étude.").
        """
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")

        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        if "company_id" in body:
            return _error(
                "COOLING_COMPANY_OVERRIDE_FORBIDDEN",
                "company_id is derived from the authenticated user and cannot be set from the API.",
                status=403,
                field="company_id",
            )

        range_error = _range_error(
            {k: v for k, v in body.items() if k in ("latitude", "longitude", "altitude_m")},
            api_validation.FIELD_LIMITS,
            section="location",
        )
        if range_error:
            return range_error

        timezone = body.get("timezone")
        if timezone and timezone not in zoneinfo.available_timezones():
            return _error(
                "GEO_INVALID_TIMEZONE",
                f"'{timezone}' is not a valid IANA timezone name.",
                status=422,
                field="timezone",
                section="location",
            )

        # README §17 "10 confirmations/minute/étude".
        limited = _check_rate_limit("confirm_location", window_seconds=60, max_count=10, study=study)
        if limited:
            return limited

        try:
            study.action_confirm_geolocation(body)
        except AccessError:
            # AccessError is itself a UserError subclass in Odoo, so it must
            # be excluded from the (UserError, ValidationError) branch below
            # explicitly and re-raised for `_guarded`'s own `except
            # AccessError` handler to map to 403 COOLING_ACCESS_DENIED —
            # otherwise a cross-user confirm-location attempt would
            # misreport as 409 "study locked" instead of "access denied".
            raise
        except (UserError, ValidationError) as exc:
            return _error("COOLING_STUDY_LOCKED", str(exc), status=409, section="studies", action="create_revision")
        return _json_response({"data": _serialize_study(study)})

    # ------------------------------------------------------------------
    # Thermal specification (GC-COOLING-08/09): geometry, envelope, facades
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/thermal-specification-templates", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def list_thermal_specification_templates(self, **kwargs):
        """The canonical GreenCube model catalog (Studio/Bureau/Habitat/
        Commerce/...): active, standard_model=True specifications a user
        can apply as the starting point for their own study (GC-COOLING-08).
        Custom/private specifications never appear here."""
        templates = request.env["greencube.thermal.specification"].search(
            [("standard_model", "=", True)], order="name, version desc"
        )
        return _json_response({"data": [_serialize_thermal_spec(t) for t in templates]})

    @http.route(
        f"{BASE}/studies/<int:study_id>/thermal-specification", type="http", auth="user", methods=["GET"], csrf=False
    )
    @_guarded
    def get_thermal_specification(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        if not study.thermal_specification_id:
            return _json_response({"data": None})
        return _json_response({"data": _serialize_thermal_spec(study.thermal_specification_id)})

    @http.route(
        f"{BASE}/studies/<int:study_id>/thermal-specification", type="http", auth="user", methods=["PUT"], csrf=False
    )
    @_guarded
    def put_thermal_specification(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)

        spec_vals = {
            k: body[k]
            for k in (
                "length_m",
                "width_m",
                "height_m",
                "wall_u_value",
                "roof_u_value",
                "floor_u_value",
                "airtightness_n50",
                "thermal_mass_level",
                "thermal_bridge_factor",
                "default_infiltration_ach",
                "product_template_id",
                "standard_model",
            )
            if k in body
        }
        range_error = _range_error(spec_vals, api_validation.FIELD_LIMITS, section="model")
        if range_error:
            return range_error
        facades = body.get("facades")
        if facades is not None:
            if not isinstance(facades, list):
                return _error("INVALID_PAYLOAD", "facades must be a JSON array.", status=400, field="facades", section="model")
            for facade in facades:
                facade_error = _range_error(
                    {
                        k: v
                        for k, v in facade.items()
                        if k in ("solar_factor_g", "visible_transmittance", "window_u_value")
                    },
                    api_validation.FIELD_LIMITS,
                    section="model",
                )
                if facade_error:
                    return facade_error

        # Provenance only (GC-COOLING-08): which catalog template, if any,
        # this private fork was based on. Never make a private spec
        # standard_model=True through this route — that stays manager-only
        # (docs/cooling_security_matrix.md).
        source_template = None
        source_template_id = body.get("source_template_id")
        if source_template_id:
            candidate = request.env["greencube.thermal.specification"].browse(int(source_template_id))
            if candidate.exists() and candidate.standard_model:
                source_template = candidate

        spec = study.thermal_specification_id
        try:
            if spec and not spec.standard_model and len(spec.study_ids) <= 1 and not spec.is_locked:
                if spec_vals:
                    spec.write(spec_vals)
                if source_template:
                    spec.write(
                        {"source_template_id": source_template.id, "source_template_version": source_template.version}
                    )
            else:
                inherited = (
                    {
                        "length_m": source_template.length_m,
                        "width_m": source_template.width_m,
                        "height_m": source_template.height_m,
                        "wall_u_value": source_template.wall_u_value,
                        "roof_u_value": source_template.roof_u_value,
                        "floor_u_value": source_template.floor_u_value,
                        "airtightness_n50": source_template.airtightness_n50,
                        "thermal_mass_level": source_template.thermal_mass_level,
                        "thermal_bridge_factor": source_template.thermal_bridge_factor,
                        "default_infiltration_ach": source_template.default_infiltration_ach,
                    }
                    if source_template
                    else {}
                )
                create_vals = {
                    "name": body.get("name") or f"{study.name} — spécification",
                    "code": f"study-{study.id}",
                    "standard_model": False,
                    "length_m": 1,
                    "width_m": 1,
                    "height_m": 1,
                    "wall_u_value": 0.3,
                    "roof_u_value": 0.3,
                    "floor_u_value": 0.3,
                    **inherited,
                    **spec_vals,
                    **(
                        {
                            "source_template_id": source_template.id,
                            "source_template_version": source_template.version,
                        }
                        if source_template
                        else {}
                    ),
                }
                spec = request.env["greencube.thermal.specification"].create(create_vals)
                study.write({"thermal_specification_id": spec.id})
                if source_template and facades is None:
                    # First fork from a catalog template: also inherit its
                    # facades so the study isn't left with zero surfaces
                    # until OrientationStep explicitly overrides them.
                    for facade in source_template.facade_ids:
                        request.env["greencube.thermal.facade"].create(
                            {
                                "thermal_specification_id": spec.id,
                                "orientation": facade.orientation,
                                "gross_area_m2": facade.gross_area_m2,
                                "glazing_area_m2": facade.glazing_area_m2,
                                "window_u_value": facade.window_u_value,
                                "solar_factor_g": facade.solar_factor_g,
                                "visible_transmittance": facade.visible_transmittance,
                                "default_shading_type": facade.default_shading_type,
                                "default_shading_factor": facade.default_shading_factor,
                            }
                        )

            if facades is not None:
                spec.facade_ids.unlink()
                for facade in facades:
                    request.env["greencube.thermal.facade"].create(
                        {
                            "thermal_specification_id": spec.id,
                            "orientation": facade["orientation"],
                            "gross_area_m2": facade.get("gross_area_m2", 0),
                            "glazing_area_m2": facade.get("glazing_area_m2", 0),
                            "window_u_value": facade.get("window_u_value"),
                            "solar_factor_g": facade.get("solar_factor_g"),
                            "visible_transmittance": facade.get("visible_transmittance"),
                            "default_shading_type": facade.get("default_shading_type", "none"),
                            "default_shading_factor": facade.get("default_shading_factor", 1.0),
                        }
                    )
        except (UserError, ValidationError) as exc:
            return _error("THERMAL_SPEC_INVALID", str(exc), status=422, section="model")

        study._invalidate_active_snapshot()
        return _json_response({"data": _serialize_thermal_spec(spec)})

    # ------------------------------------------------------------------
    # Occupancy profile (GC-COOLING-10)
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies/<int:study_id>/occupancy-profile", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def get_occupancy_profile(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        profile = study.occupancy_profile_ids[:1]
        return _json_response({"data": _serialize_occupancy(profile) if profile else None})

    @http.route(f"{BASE}/studies/<int:study_id>/occupancy-profile", type="http", auth="user", methods=["PUT"], csrf=False)
    @_guarded
    def put_occupancy_profile(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        vals = {
            k: body[k]
            for k in (
                "usage_type",
                "usual_occupants",
                "maximum_occupants",
                "activity_level",
                "usage_days",
                "active_monday",
                "active_tuesday",
                "active_wednesday",
                "active_thursday",
                "active_friday",
                "active_saturday",
                "active_sunday",
                "start_hour",
                "end_hour",
                "used_at_night",
                "sensible_gain_per_person_w",
                "latent_gain_per_person_g_h",
                "lighting_power_density_wm2",
                "lighting_usage_fraction",
                "provenance",
            )
            if k in body
        }
        range_error = _range_error(vals, api_validation.FIELD_LIMITS, section="usage")
        if range_error:
            return range_error
        try:
            profile = study.occupancy_profile_ids[:1]
            if profile:
                profile.write(vals)
            else:
                profile = request.env["greencube.cooling.occupancy.profile"].create({**vals, "study_id": study.id})
        except UserError as exc:
            # Raised by occupancy_profile.write()/create() when the parent
            # study is validated (GC-COOLING-10): a validated study is a
            # frozen record, direct edits must go through a revision.
            return _error("INVALID_STATE", str(exc), status=409, section="usage", action="create_revision")
        except ValidationError as exc:
            return _error("OCCUPANCY_PROFILE_INVALID", str(exc), status=422, section="usage")
        study._invalidate_active_snapshot()
        return _json_response({"data": _serialize_occupancy(profile)})

    # ------------------------------------------------------------------
    # Ventilation profile (GC-COOLING-12)
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies/<int:study_id>/ventilation-profile", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def get_ventilation_profile(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        profile = study.ventilation_profile_ids[:1]
        return _json_response({"data": _serialize_ventilation(profile) if profile else None})

    @http.route(f"{BASE}/studies/<int:study_id>/ventilation-profile", type="http", auth="user", methods=["PUT"], csrf=False)
    @_guarded
    def put_ventilation_profile(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        vals = {
            k: body[k]
            for k in (
                "ventilation_type",
                "airflow_m3h",
                "air_changes_per_hour",
                "heat_recovery_efficiency_percent",
                "door_opening_frequency",
                "window_opening_frequency",
                "airtightness_n50",
                "wind_exposure",
                "infiltration_ach",
                "fan_power_w",
                "fan_fraction_dissipated_in_zone",
                "bypass_active",
                "provenance",
            )
            if k in body
        }
        range_error = _range_error(vals, api_validation.FIELD_LIMITS, section="comfort")
        if range_error:
            return range_error
        try:
            profile = study.ventilation_profile_ids[:1]
            if profile:
                profile.write(vals)
            else:
                profile = request.env["greencube.cooling.ventilation.profile"].create({**vals, "study_id": study.id})
        except UserError as exc:
            # Raised by ventilation_profile.write()/create() when the parent
            # study is validated (GC-COOLING-12): a validated study is a
            # frozen record, direct edits must go through a revision.
            return _error("INVALID_STATE", str(exc), status=409, section="comfort", action="create_revision")
        except ValidationError as exc:
            return _error("VENTILATION_PROFILE_INVALID", str(exc), status=422, section="comfort")
        study._invalidate_active_snapshot()
        return _json_response({"data": _serialize_ventilation(profile)})

    # ------------------------------------------------------------------
    # Solar shading (GC-COOLING-09)
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies/<int:study_id>/shading", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def get_shading(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": [_serialize_shading(s) for s in study.shading_ids]})

    @http.route(f"{BASE}/studies/<int:study_id>/shading", type="http", auth="user", methods=["PUT"], csrf=False)
    @_guarded
    def put_shading(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body()
        if not isinstance(body, list):
            return _error("INVALID_JSON", "Request body must be a JSON array of shading entries.", status=400)
        for entry in body:
            entry_error = _range_error(
                {k: v for k, v in entry.items() if k == "efficiency_percent"},
                api_validation.FIELD_LIMITS,
                section="orientation",
            )
            if entry_error:
                return entry_error
        try:
            study.shading_ids.unlink()
            for entry in body:
                request.env["greencube.cooling.shading"].create(
                    {
                        "study_id": study.id,
                        "orientation": entry["orientation"],
                        "shading_type": entry.get("shading_type", "none"),
                        "efficiency_percent": entry.get("efficiency_percent", 0),
                        "start_hour": entry.get("start_hour", 0),
                        "end_hour": entry.get("end_hour", 24),
                        "automatic": entry.get("automatic", False),
                        "confirmed": entry.get("confirmed", False),
                        "provenance": entry.get("provenance", "user_confirmed"),
                    }
                )
        except (UserError, ValidationError) as exc:
            return _error("SHADING_INVALID", str(exc), status=422, section="orientation")
        study._invalidate_active_snapshot()
        return _json_response({"data": [_serialize_shading(s) for s in study.shading_ids]})

    # ------------------------------------------------------------------
    # Equipment loads (GC-COOLING-11)
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-loads", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def list_equipment_loads(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": [_serialize_equipment_load(e) for e in study.equipment_load_ids]})

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-loads", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def create_equipment_load(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        equip_vals = _equipment_load_vals(body)
        range_error = _range_error(equip_vals, api_validation.FIELD_LIMITS, section="equipment")
        if range_error:
            return range_error
        try:
            line = request.env["greencube.cooling.equipment.load"].create({**equip_vals, "study_id": study.id})
        except ValidationError as exc:
            return _error("EQUIPMENT_LOAD_INVALID", str(exc), status=422, section="equipment")
        study._invalidate_active_snapshot()
        return _json_response({"data": _serialize_equipment_load(line)}, status=201)

    @http.route(f"{BASE}/equipment-loads/<int:line_id>", type="http", auth="user", methods=["PATCH"], csrf=False)
    @_guarded
    def update_equipment_load(self, line_id, **kwargs):
        line = request.env["greencube.cooling.equipment.load"].browse(line_id)
        if not line.exists():
            return _error("EQUIPMENT_LOAD_NOT_FOUND", "Equipment load not found.", status=404, section="equipment")
        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        equip_vals = _equipment_load_vals(body)
        range_error = _range_error(equip_vals, api_validation.FIELD_LIMITS, section="equipment")
        if range_error:
            return range_error
        try:
            line.write(equip_vals)
        except ValidationError as exc:
            return _error("EQUIPMENT_LOAD_INVALID", str(exc), status=422, section="equipment")
        line.study_id._invalidate_active_snapshot()
        return _json_response({"data": _serialize_equipment_load(line)})

    @http.route(f"{BASE}/equipment-loads/<int:line_id>", type="http", auth="user", methods=["DELETE"], csrf=False)
    @_guarded
    def delete_equipment_load(self, line_id, **kwargs):
        line = request.env["greencube.cooling.equipment.load"].browse(line_id)
        if not line.exists():
            return _error("EQUIPMENT_LOAD_NOT_FOUND", "Equipment load not found.", status=404, section="equipment")
        study = line.study_id
        line.unlink()
        study._invalidate_active_snapshot()
        return _json_response({"data": {"deleted": True}})

    # ------------------------------------------------------------------
    # Revisions / validation / snapshot / calculation
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies/<int:study_id>/revisions", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def create_revision(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        try:
            action = study.action_create_revision()
        except UserError as exc:
            return _error("COOLING_REVISION_FORBIDDEN", str(exc), status=403, section="studies")
        revision = request.env["greencube.cooling.study"].browse(action["res_id"])
        return _json_response({"data": _serialize_study(revision)}, status=201)

    @http.route(f"{BASE}/studies/<int:study_id>/validate", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def validate_study(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        try:
            study.action_validate()
        except UserError as exc:
            return _error("COOLING_VALIDATION_FORBIDDEN", str(exc), status=403, section="studies")
        return _json_response({"data": _serialize_study(study)})

    @http.route(f"{BASE}/studies/<int:study_id>/validation", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def get_study_validation(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": study.get_validation()})

    @http.route(
        f"{BASE}/studies/<int:study_id>/assumptions/confirm", type="http", auth="user", methods=["POST"], csrf=False
    )
    @_guarded
    def confirm_assumptions(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        try:
            count = study.action_confirm_assumptions()
        except UserError as exc:
            return _error("COOLING_ASSUMPTION_CONFIRMATION_FAILED", str(exc), status=422, section="review")
        return _json_response({"data": {"study_id": study.id, "confirmed_count": count}})

    @http.route(f"{BASE}/studies/<int:study_id>/snapshots", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def create_snapshot(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        try:
            snapshot_hash = study.action_create_snapshot()
        except UserError as exc:
            return _error("COOLING_STUDY_INCOMPLETE", str(exc), status=422, section="review")
        return _json_response({"data": {"study_id": study.id, "snapshot_hash": snapshot_hash}}, status=201)

    @http.route(f"{BASE}/studies/<int:study_id>/ready", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def mark_study_ready(self, study_id, **kwargs):
        """GC-COOLING-13: 'faire passer l'étude au statut ready' -- the
        review screen's own confirmation button never flips this locally;
        this route re-runs get_validation()'s blocking rules server-side
        (via action_mark_ready()) before honoring the transition."""
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")

        if_match = request.httprequest.headers.get("If-Match")
        current_version = study.write_date.isoformat() if study.write_date else None
        if if_match and current_version and if_match != current_version:
            return _error(
                "COOLING_STUDY_VERSION_CONFLICT",
                "This study was modified by someone else since it was last read. Reload and retry.",
                status=409,
                section="studies",
            )

        try:
            study.action_mark_ready()
        except (UserError, ValidationError) as exc:
            return _error("COOLING_STUDY_LOCKED", str(exc), status=409, section="studies", action="create_revision")

        if study.state != "ready":
            validation = study.get_validation()
            blocking_messages = [issue["message"] for issue in validation["issues"] if issue["blocking"]]
            return _error(
                "STUDY_INCOMPLETE",
                "Cannot mark this study ready: " + "; ".join(blocking_messages),
                status=422,
                section="review",
            )
        return _json_response({"data": _serialize_study(study)})

    @http.route(f"{BASE}/studies/<int:study_id>/calculations", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def create_calculation(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body() or {}
        engine = body.get("engine") if body.get("engine") in ("quick_solver", "energyplus", "both") else None
        idempotency_key = request.httprequest.headers.get("Idempotency-Key")
        limited = _check_rate_limit("calculate", window_seconds=3600, max_count=10, study=study)
        if limited:
            return limited
        try:
            result = study.action_calculate(engine=engine, idempotency_key=idempotency_key)
        except CoolingIdempotencyConflict as exc:
            return _error("IDEMPOTENCY_CONFLICT", str(exc), status=409, section="results")
        except UserError as exc:
            return _error("COOLING_CALCULATION_FAILED", str(exc), status=422, section="results")
        # action_calculate() always creates a greencube.cooling.calculation.job
        # (GC-COOLING-15 pt.1) except on the idempotency-key fast path, which
        # returns the original call's result without creating a new job —
        # look the original job up by result_id either way, so job_id is
        # always a real job record, never the result id standing in for one.
        job = request.env["greencube.cooling.calculation.job"].search(
            [("result_id", "=", result.id)], limit=1, order="create_date desc"
        )
        return _json_response(
            {
                "data": {
                    "job_id": job.id if job else result.id,
                    "status": job.status if job else "completed",
                    "result_id": result.id,
                    "engine": "MERCURE",
                    "engine_version": result.solver_version_id.version if result.solver_version_id else None,
                    "energyplus_processing_status": job.energyplus_processing_status if job else "not_requested",
                    "request_id": _request_id(),
                }
            },
            status=201,
        )

    @http.route(f"{BASE}/calculations/<int:job_id>", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def get_calculation(self, job_id, **kwargs):
        job = request.env["greencube.cooling.calculation.job"].browse(job_id)
        if not job.exists():
            return _error("COOLING_JOB_NOT_FOUND", "Calculation job not found.", status=404, section="results")
        return _json_response(
            {
                "data": {
                    "job_id": job.id,
                    "status": job.status,
                    "result_id": job.result_id.id if job.result_id else None,
                    "energyplus_processing_status": job.energyplus_processing_status,
                    "error_message": job.error_message or None,
                }
            }
        )

    @http.route(f"{BASE}/calculations/<int:job_id>/cancel", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def cancel_calculation(self, job_id, **kwargs):
        """Cancels the EnergyPlus side of a job while it is still waiting
        for a worker to claim it (GC-COOLING-15). `browse` (not `sudo()`)
        so ir.rule enforces the caller's own ownership/company scope the
        same way as GET /calculations/<id> just above — `_guarded` maps the
        resulting AccessError to a 404, never a bare 500/403 leak."""
        job = request.env["greencube.cooling.calculation.job"].browse(job_id)
        if not job.exists():
            return _error("COOLING_JOB_NOT_FOUND", "Calculation job not found.", status=404, section="results")
        # Force the ir.rule ownership/company check the same way GET
        # /calculations/<id> does (by reading a field) *before* attempting
        # the state-transition write below — action_cancel_energyplus()'s
        # own read of energyplus_processing_status happens inside a method
        # call and must not be the first place a cross-tenant AccessError
        # can surface, so the caller cannot distinguish "not yours" from
        # "wrong state" by status code alone.
        job.status  # noqa: B018 - deliberate access-rule probe, see above
        try:
            job.action_cancel_energyplus()
        except UserError as exc:
            return _error("COOLING_JOB_NOT_CANCELLABLE", str(exc), status=409, section="results")
        return _json_response(
            {"data": {"job_id": job.id, "energyplus_processing_status": job.energyplus_processing_status}}
        )

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/results/<int:result_id>", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def get_result(self, result_id, **kwargs):
        result = request.env["greencube.cooling.result"].browse(result_id)
        if not result.exists():
            return _error("COOLING_RESULT_NOT_FOUND", "Result not found.", status=404, section="results")
        return _json_response({"data": _serialize_result(result)})

    @http.route(f"{BASE}/studies/<int:study_id>/results", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def list_results(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": [_serialize_result(r) for r in study.result_ids]})

    # ------------------------------------------------------------------
    # Equipment
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/equipment-catalog", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def equipment_catalog(self, **kwargs):
        products = request.env["product.template"].search([("is_cooling_equipment", "=", True)])
        return _json_response({"data": [_serialize_product(p) for p in products]})

    @http.route(f"{BASE}/equipment-load-catalog", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def equipment_load_catalog(self, **kwargs):
        # Internal-loads (equipment/lighting/appliances) reference catalog
        # for the Equipment step (GC-COOLING-11): distinct from
        # equipment_catalog() above, which lists cooling equipment *to
        # install*, not the internal loads a study's premises already
        # contain.
        products = request.env["product.template"].search([("is_internal_load_equipment", "=", True)])
        return _json_response({"data": [_serialize_internal_load_product(p) for p in products]})

    def _stale_result_error(self, result):
        """GC-COOLING-18 acceptance criterion: "un résultat obsolète bloque
        la sélection". A result whose frozen snapshot has since been
        superseded (the study's inputs were edited after this result was
        computed) must not silently be used to recommend/select equipment
        as if it were still current.
        """
        if result.snapshot_id and result.snapshot_id.state != "frozen":
            return _error(
                "COOLING_RESULT_STALE",
                "This study's inputs changed since the last calculation; recalculate before selecting equipment.",
                status=422,
                section="equipment-selection",
                action="create_calculation",
            )
        return None

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-recommendations", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def equipment_recommendations(self, study_id, **kwargs):
        from ..services.compatibility import ProductTechnicalData, assess_compatibility, recommendation_sort_key

        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        result = study.active_result_id
        if not result:
            return _error("COOLING_RESULT_MISSING", "No active result for this study.", status=422, section="equipment-selection", action="create_calculation")
        stale_error = self._stale_result_error(result)
        if stale_error:
            return stale_error

        products = request.env["product.template"].search([("is_cooling_equipment", "=", True)])
        rows = []
        for product in products:
            technical = ProductTechnicalData(
                capacity_at_45c_w=product.capacity_at_45c_w,
                max_outdoor_temperature_c=product.max_outdoor_temperature_c,
                shr=product.cooling_shr,
            )
            assessment = assess_compatibility(technical, result.recommended_capacity_w, result.shr)
            rows.append((assessment, product))
        # Robust, stable ranking (GC-COOLING-18 audit finding): a naive
        # ascending sort on oversizing_ratio put products with missing/zero
        # technical data first, since they used to compute as ratio 0.0.
        rows.sort(key=lambda pair: recommendation_sort_key(pair[0], pair[1].id))
        recommendations = [
            {
                "product": _serialize_product(product),
                "status": assessment.status,
                "reasons": assessment.reasons,
                "oversizing_ratio": assessment.oversizing_ratio,
            }
            for assessment, product in rows
        ]
        return _json_response({"data": recommendations})

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-selections", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def list_equipment_selections(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": [_serialize_equipment_selection(s) for s in study.equipment_selection_ids]})

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-selections", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def create_equipment_selection(self, study_id, **kwargs):
        from ..services.compatibility import ProductTechnicalData, assess_compatibility

        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body()
        if not body or "product_id" not in body:
            return _error("INVALID_PAYLOAD", "product_id is required.", status=400, field="product_id")

        result = study.active_result_id
        if not result:
            return _error("COOLING_RESULT_MISSING", "No active result for this study.", status=422, section="equipment-selection", action="create_calculation")
        stale_error = self._stale_result_error(result)
        if stale_error:
            return stale_error

        product = request.env["product.template"].browse(body["product_id"])
        if not product.exists() or not product.is_cooling_equipment:
            return _error("COOLING_PRODUCT_NOT_FOUND", "Product not found.", status=404, field="product_id")

        technical = ProductTechnicalData(
            capacity_at_45c_w=product.capacity_at_45c_w,
            max_outdoor_temperature_c=product.max_outdoor_temperature_c,
            shr=product.cooling_shr,
        )
        assessment = assess_compatibility(technical, result.recommended_capacity_w, result.shr)
        if assessment.status == "incompatible":
            return _error(
                "COOLING_PRODUCT_INCOMPATIBLE",
                "This product is incompatible with the recommended cooling load.",
                status=422,
                field="product_id",
            )
        if assessment.status == "insufficient_data":
            return _error(
                "COOLING_PRODUCT_DATA_INCOMPLETE",
                "This product does not have enough technical data to be selected: "
                + ", ".join(assessment.missing_fields) + ".",
                status=422,
                field="product_id",
            )

        # A new choice substitutes whichever prior selection is still the
        # study's "current" one — either a working "selected" draft (which
        # this flips to "superseded") or an already-"validated" commercial
        # record (which, per equipment_selection.py's immutability
        # guarantee, can never be moved to "superseded" and simply stays
        # "validated" as permanent history). Either way `supersedes_id`
        # links the new row back to it (spec §"Historique et versioning").
        previous = study.equipment_selection_ids.filtered(lambda s: s.state in ("selected", "validated"))
        previous.filtered(lambda s: s.state == "selected").write({"state": "superseded"})
        product_variant = product.product_variant_id
        selection = request.env["greencube.cooling.equipment.selection"].create(
            {
                "study_id": study.id,
                "result_id": result.id,
                "product_id": product_variant.id,
                "compatibility_status": assessment.status,
                "state": "selected",
                "price": product.list_price,
                "supersedes_id": previous[:1].id if previous else False,
                # Frozen at selection time — audit P1-08: without this, a
                # historical selection would silently reflect today's
                # catalog data (name/specs can change or be archived) rather
                # than what was actually assessed when chosen.
                "product_name": product.name,
                "capacity_at_45c_w": product.capacity_at_45c_w,
                "max_outdoor_temperature_c": product.max_outdoor_temperature_c,
                "shr": product.cooling_shr,
                "eer": product.eer,
                "nominal_capacity_w": product.nominal_capacity_w,
            }
        )
        return _json_response(
            {"data": _serialize_equipment_selection(selection)},
            status=201,
        )

    @http.route(
        f"{BASE}/studies/<int:study_id>/equipment-selections/<int:selection_id>/validate",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    @_guarded
    def validate_equipment_selection(self, study_id, selection_id, **kwargs):
        """Promotes a "selected" equipment choice to an immutable
        "validated" commercial record (GC-COOLING-18 §"Sélection finale").
        Without this route the frontend had no way to ever reach the
        `validated` state, so equipment_selection.py's immutability guard
        never actually engaged.
        """
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        # ir.rule already scopes `search`/`browse` to the caller's own
        # studies (or their company, for technicians); looking the
        # selection up *through* the study's own one2many instead of a bare
        # browse() additionally guarantees the selection actually belongs
        # to the study in the URL, not just to some study the caller can
        # see (IDOR across two of the caller's own studies).
        selection = study.equipment_selection_ids.filtered(lambda s: s.id == selection_id)
        if not selection:
            return _error("COOLING_SELECTION_NOT_FOUND", "Equipment selection not found.", status=404, section="equipment-selection")
        if selection.state != "selected":
            return _error(
                "COOLING_SELECTION_ALREADY_EXISTS",
                f"This selection is already in state '{selection.state}' and cannot be validated again.",
                status=409,
                section="equipment-selection",
            )
        selection.action_validate()
        return _json_response({"data": _serialize_equipment_selection(selection)})

    # ------------------------------------------------------------------
    # EnergyPlus worker hand-off (GC-COOLING-15)
    #
    # These two routes are the ONLY way the standalone energyplus_worker/
    # process talks to Odoo — it never opens a PostgreSQL connection itself.
    # They use `auth="public"` plus a shared-secret header instead of
    # `auth="user"`/session cookies, since a headless worker has no
    # interactive Odoo session to authenticate with. This is a narrower
    # trust boundary than a logged-in user: the worker key grants exactly
    # "claim/complete EnergyPlus jobs", nothing else, and every write here
    # goes through `sudo()` deliberately scoped to that.
    # ------------------------------------------------------------------

    def _check_worker_key(self):
        configured = request.env["ir.config_parameter"].sudo().get_param("greencube_cooling.energyplus_worker_key")
        if not configured:
            # Secure-by-default: an unset key disables the endpoint rather
            # than accepting any request. An operator must deliberately set
            # it (env var GC_COOLING_ENERGYPLUS_WORKER_KEY -> config
            # parameter, see energyplus_worker/README.md) before a worker
            # can be deployed at all.
            return _error(
                "ENERGYPLUS_WORKER_NOT_CONFIGURED",
                "No worker key is configured; the EnergyPlus worker endpoints are disabled.",
                status=503,
            )
        provided = request.httprequest.headers.get("X-GreenCube-Worker-Key")
        if not provided or provided != configured:
            return _error("ENERGYPLUS_WORKER_UNAUTHORIZED", "Invalid or missing worker key.", status=401)
        return None

    @http.route(f"{BASE}/energyplus-jobs/claim", type="http", auth="public", methods=["POST"], csrf=False)
    def claim_energyplus_job(self, **kwargs):
        denied = self._check_worker_key()
        if denied:
            return denied

        job = request.env["greencube.cooling.calculation.job"].sudo()._claim_next_for_worker()
        if not job:
            return _json_response({"data": None}, status=204)

        return _json_response(
            {
                "data": {
                    "job_id": job.id,
                    "study_id": job.study_id.id,
                    "snapshot_hash": job.snapshot_id.snapshot_hash,
                    "payload_json": job.snapshot_id.payload_json,
                }
            }
        )

    @http.route(f"{BASE}/energyplus-jobs/<int:job_id>/complete", type="http", auth="public", methods=["POST"], csrf=False)
    def complete_energyplus_job(self, job_id, **kwargs):
        denied = self._check_worker_key()
        if denied:
            return denied

        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        status = body.get("status")
        if status not in ("simulation_completed", "simulation_unavailable", "simulation_failed"):
            return _error(
                "INVALID_PAYLOAD",
                "status must be one of simulation_completed, simulation_unavailable, simulation_failed.",
                status=400,
                field="status",
            )

        job = request.env["greencube.cooling.calculation.job"].sudo().browse(job_id)
        if not job.exists():
            return _error("COOLING_JOB_NOT_FOUND", "Calculation job not found.", status=404)

        try:
            job._complete_from_worker(status, detail=body.get("detail"))
        except UserError as exc:
            return _error("ENERGYPLUS_JOB_STATE_CONFLICT", str(exc), status=409)

        for artifact in body.get("artifacts", []):
            required = {"artifact_type", "checksum_sha256", "filename", "content_b64"}
            if not required <= artifact.keys():
                return _error(
                    "INVALID_PAYLOAD",
                    f"Each artifact requires {sorted(required)}.",
                    status=400,
                    field="artifacts",
                )
            attachment = request.env["ir.attachment"].sudo().create(
                {
                    "name": artifact["filename"],
                    "type": "binary",
                    "datas": artifact["content_b64"],
                    "res_model": "greencube.cooling.calculation.job",
                    "res_id": job.id,
                }
            )
            request.env["greencube.cooling.simulation.artifact"].sudo().create(
                {
                    "job_id": job.id,
                    "artifact_type": artifact["artifact_type"],
                    "checksum_sha256": artifact["checksum_sha256"],
                    "attachment_id": attachment.id,
                }
            )

        return _json_response({"data": {"job_id": job.id, "energyplus_processing_status": job.energyplus_processing_status}})
