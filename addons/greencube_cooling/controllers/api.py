# -*- coding: utf-8 -*-
"""JSON API for GreenCube Cooling, per README_GC-COOLING-02_API_ODOO.md.

Routes are intentionally thin: they validate the request, delegate to the
model layer (which owns all business rules), and serialize the response.
No thermal logic lives here — MERCURE stays independent of the ORM and of
this controller.
"""
import functools
import json
import uuid

from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request

from ..services import geo as geo_service

BASE = "/api/v1/greencube/cooling"


def _request_id():
    return f"req-{uuid.uuid4()}"


def _json_response(payload, status=200):
    return request.make_response(
        json.dumps(payload, default=str),
        status=status,
        headers=[("Content-Type", "application/json")],
    )


def _error(code, message, status=400, field=None, section=None, action=None):
    return _json_response(
        {
            "error": {
                "code": code,
                "message": message,
                "field": field,
                "section": section,
                "action": action,
                "request_id": _request_id(),
            }
        },
        status=status,
    )


def _guarded(fn):
    """Turns ir.rule ownership violations into the standard JSON error
    envelope instead of Odoo's default HTML/plain error page. Every route
    handler on this controller is wrapped with this, since sub-resources
    (occupancy, equipment, results, ...) are addressed directly by numeric
    id and rely entirely on ir.rule for ownership enforcement (audit
    P0-05)."""

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except AccessError as exc:
            return _error("COOLING_ACCESS_DENIED", str(exc), status=403)
        except MissingError as exc:
            return _error("COOLING_NOT_FOUND", str(exc), status=404)

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
            "environment_type": study.environment_type or None,
            "climate_confirmed": study.climate_confirmed,
            "main_orientation": study.main_orientation or None,
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
        "usage_days": profile.usage_days,
        "start_hour": profile.start_hour,
        "end_hour": profile.end_hour,
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
        "infiltration_ach": profile.infiltration_ach,
        "fan_power_w": profile.fan_power_w,
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
    return {
        "id": result.id,
        "study_id": result.study_id.id,
        "engine": "MERCURE",
        "engine_version": result.solver_version_id.version if result.solver_version_id else None,
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
    }


class GreencubeCoolingApiController(http.Controller):

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
        try:
            study.write(vals)
        except (UserError, ValidationError) as exc:
            return _error("COOLING_STUDY_LOCKED", str(exc), status=409, section="studies", action="create_revision")
        return _json_response({"data": _serialize_study(study)})

    # ------------------------------------------------------------------
    # Geolocation (GC-COOLING-03): address search, altitude, timezone
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/geocode", type="http", auth="user", methods=["GET"], csrf=False)
    @_guarded
    def geocode(self, query=None, **kwargs):
        if not query or not query.strip():
            return _error("GEOCODE_QUERY_REQUIRED", "A non-empty 'query' parameter is required.", status=400, field="query")
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
        try:
            context = request.env["greencube.cooling.geo.cache"].get_or_fetch_context(lat, lon)
        except geo_service.GeoServiceError as exc:
            return _error("GEO_PROVIDER_UNAVAILABLE", str(exc), status=502, section="location")
        return _json_response({"data": context})

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
        facades = body.get("facades")

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
        try:
            profile = study.occupancy_profile_ids[:1]
            if profile:
                profile.write(vals)
            else:
                profile = request.env["greencube.cooling.occupancy.profile"].create({**vals, "study_id": study.id})
        except ValidationError as exc:
            return _error("OCCUPANCY_PROFILE_INVALID", str(exc), status=422, section="usage")
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
                "infiltration_ach",
                "fan_power_w",
                "bypass_active",
                "provenance",
            )
            if k in body
        }
        try:
            profile = study.ventilation_profile_ids[:1]
            if profile:
                profile.write(vals)
            else:
                profile = request.env["greencube.cooling.ventilation.profile"].create({**vals, "study_id": study.id})
        except ValidationError as exc:
            return _error("VENTILATION_PROFILE_INVALID", str(exc), status=422, section="comfort")
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
        try:
            line = request.env["greencube.cooling.equipment.load"].create({**_equipment_load_vals(body), "study_id": study.id})
        except ValidationError as exc:
            return _error("EQUIPMENT_LOAD_INVALID", str(exc), status=422, section="equipment")
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
        try:
            line.write(_equipment_load_vals(body))
        except ValidationError as exc:
            return _error("EQUIPMENT_LOAD_INVALID", str(exc), status=422, section="equipment")
        return _json_response({"data": _serialize_equipment_load(line)})

    @http.route(f"{BASE}/equipment-loads/<int:line_id>", type="http", auth="user", methods=["DELETE"], csrf=False)
    @_guarded
    def delete_equipment_load(self, line_id, **kwargs):
        line = request.env["greencube.cooling.equipment.load"].browse(line_id)
        if not line.exists():
            return _error("EQUIPMENT_LOAD_NOT_FOUND", "Equipment load not found.", status=404, section="equipment")
        line.unlink()
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

    @http.route(f"{BASE}/studies/<int:study_id>/calculations", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def create_calculation(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        body = _body() or {}
        engine = body.get("engine") if body.get("engine") in ("quick_solver", "energyplus", "both") else None
        idempotency_key = request.httprequest.headers.get("Idempotency-Key")
        try:
            result = study.action_calculate(engine=engine, idempotency_key=idempotency_key)
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

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-recommendations", type="http", auth="user", methods=["POST"], csrf=False)
    @_guarded
    def equipment_recommendations(self, study_id, **kwargs):
        from ..services.compatibility import ProductTechnicalData, assess_compatibility

        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        result = study.active_result_id
        if not result:
            return _error("COOLING_RESULT_MISSING", "No active result for this study.", status=422, section="equipment-selection", action="create_calculation")

        products = request.env["product.template"].search([("is_cooling_equipment", "=", True)])
        recommendations = []
        for product in products:
            technical = ProductTechnicalData(
                capacity_at_45c_w=product.capacity_at_45c_w,
                max_outdoor_temperature_c=product.max_outdoor_temperature_c,
                shr=product.cooling_shr,
            )
            assessment = assess_compatibility(technical, result.recommended_capacity_w, result.shr)
            recommendations.append(
                {
                    "product": _serialize_product(product),
                    "status": assessment.status,
                    "reasons": assessment.reasons,
                    "oversizing_ratio": assessment.oversizing_ratio,
                }
            )
        recommendations.sort(key=lambda r: r["oversizing_ratio"])
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

        product = request.env["product.template"].browse(body["product_id"])
        if not product.exists():
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

        study.equipment_selection_ids.filtered(lambda s: s.state == "selected").write({"state": "superseded"})
        product_variant = product.product_variant_id
        selection = request.env["greencube.cooling.equipment.selection"].create(
            {
                "study_id": study.id,
                "result_id": result.id,
                "product_id": product_variant.id,
                "compatibility_status": assessment.status,
                "state": "selected",
                "price": product.list_price,
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
