# -*- coding: utf-8 -*-
"""JSON API for GreenCube Cooling, per README_GC-COOLING-02_API_ODOO.md.

Routes are intentionally thin: they validate the request, delegate to the
model layer (which owns all business rules), and serialize the response.
No thermal logic lives here — MERCURE stays independent of the ORM and of
this controller.
"""
import json
import uuid

from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

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
            "latitude": study.latitude or None,
            "longitude": study.longitude or None,
            "altitude_m": study.altitude_m or None,
            "environment_type": study.environment_type or None,
            "climate_confirmed": study.climate_confirmed,
        },
        "comfort": {
            "cooling_setpoint_c": study.cooling_setpoint_c,
            "target_humidity_percent": study.target_humidity_percent,
            "service_level": study.service_level,
        },
        "confidence_score": study.confidence_score,
        "input_snapshot_hash": study.input_snapshot_hash or None,
        "active_result_id": study.active_result_id.id or None,
        "updated_at": study.write_date.isoformat() if study.write_date else None,
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


class GreencubeCoolingApiController(http.Controller):

    # ------------------------------------------------------------------
    # Studies
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies", type="http", auth="user", methods=["GET"], csrf=False)
    def list_studies(self, **kwargs):
        studies = request.env["greencube.cooling.study"].search([], order="create_date desc", limit=100)
        return _json_response({"data": [_serialize_study(s) for s in studies]})

    @http.route(f"{BASE}/studies", type="http", auth="user", methods=["POST"], csrf=False)
    def create_study(self, **kwargs):
        body = _body()
        if body is None:
            return _error("INVALID_JSON", "Request body must be valid JSON.", status=400)
        name = body.get("name") or "New study"
        study = request.env["greencube.cooling.study"].create({"name": name})
        return _json_response({"data": _serialize_study(study)}, status=201)

    @http.route(f"{BASE}/studies/<int:study_id>", type="http", auth="user", methods=["GET"], csrf=False)
    def get_study(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": _serialize_study(study)})

    @http.route(f"{BASE}/studies/<int:study_id>", type="http", auth="user", methods=["PATCH"], csrf=False)
    def patch_study(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
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
            "cooling_setpoint_c",
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
    # Revisions / validation / snapshot / calculation
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/studies/<int:study_id>/revisions", type="http", auth="user", methods=["POST"], csrf=False)
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
    def validate_study(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        try:
            study.action_validate()
        except UserError as exc:
            return _error("COOLING_VALIDATION_FORBIDDEN", str(exc), status=403, section="studies")
        return _json_response({"data": _serialize_study(study)})

    @http.route(f"{BASE}/studies/<int:study_id>/snapshots", type="http", auth="user", methods=["POST"], csrf=False)
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
    def create_calculation(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        try:
            result = study.action_calculate()
        except UserError as exc:
            return _error("COOLING_CALCULATION_FAILED", str(exc), status=422, section="results")
        return _json_response(
            {
                "data": {
                    "job_id": result.id,
                    "status": "completed",
                    "result_id": result.id,
                    "engine": "MERCURE",
                    "engine_version": result.solver_version_id.version if result.solver_version_id else None,
                    "request_id": _request_id(),
                }
            },
            status=201,
        )

    @http.route(f"{BASE}/calculations/<int:job_id>", type="http", auth="user", methods=["GET"], csrf=False)
    def get_calculation(self, job_id, **kwargs):
        result = request.env["greencube.cooling.result"].browse(job_id)
        if not result.exists():
            return _error("COOLING_JOB_NOT_FOUND", "Calculation job not found.", status=404, section="results")
        return _json_response(
            {"data": {"job_id": result.id, "status": "completed", "result_id": result.id}}
        )

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/results/<int:result_id>", type="http", auth="user", methods=["GET"], csrf=False)
    def get_result(self, result_id, **kwargs):
        result = request.env["greencube.cooling.result"].browse(result_id)
        if not result.exists():
            return _error("COOLING_RESULT_NOT_FOUND", "Result not found.", status=404, section="results")
        return _json_response({"data": _serialize_result(result)})

    @http.route(f"{BASE}/studies/<int:study_id>/results", type="http", auth="user", methods=["GET"], csrf=False)
    def list_results(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response({"data": [_serialize_result(r) for r in study.result_ids]})

    # ------------------------------------------------------------------
    # Equipment
    # ------------------------------------------------------------------

    @http.route(f"{BASE}/equipment-catalog", type="http", auth="user", methods=["GET"], csrf=False)
    def equipment_catalog(self, **kwargs):
        products = request.env["product.template"].search([("is_cooling_equipment", "=", True)])
        return _json_response({"data": [_serialize_product(p) for p in products]})

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-recommendations", type="http", auth="user", methods=["POST"], csrf=False)
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
    def list_equipment_selections(self, study_id, **kwargs):
        study = request.env["greencube.cooling.study"].browse(study_id)
        if not study.exists():
            return _error("COOLING_STUDY_NOT_FOUND", "Study not found.", status=404, section="studies")
        return _json_response(
            {
                "data": [
                    {
                        "id": s.id,
                        "product_id": s.product_id.id,
                        "product_name": s.product_id.name,
                        "compatibility_status": s.compatibility_status,
                        "state": s.state,
                        "result_id": s.result_id.id,
                        "created_at": s.create_date.isoformat() if s.create_date else None,
                    }
                    for s in study.equipment_selection_ids
                ]
            }
        )

    @http.route(f"{BASE}/studies/<int:study_id>/equipment-selections", type="http", auth="user", methods=["POST"], csrf=False)
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
            }
        )
        return _json_response(
            {
                "data": {
                    "id": selection.id,
                    "product_id": product.id,
                    "compatibility_status": selection.compatibility_status,
                    "state": selection.state,
                }
            },
            status=201,
        )
