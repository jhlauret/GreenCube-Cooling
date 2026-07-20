# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import logging
import time

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.climate import ClimateServiceError, radiation_wm2_from_daily_sum
from ..services.energyplus import is_energyplus_enabled
from ..services.mercure import schemas as ms
from ..services.mercure.engine import MercureError, run_mercure
from ..services.mercure.honeybee_translator import HoneybeeTranslationError, build_honeybee_model
from ..services.mercure.serialization import mercure_input_from_dict, mercure_input_to_dict

_logger = logging.getLogger(__name__)

NON_CONFIRMED_PROVENANCES = ("estimated_reference", "estimated_manual", "missing_fallback")

STATES = [
    ("draft", "Draft"),
    ("incomplete", "Incomplete"),
    ("ready", "Ready"),
    ("calculating", "Calculating"),
    ("calculated", "Calculated"),
    ("validated", "Validated"),
    ("failed", "Failed"),
    ("archived", "Archived"),
]

SERVICE_LEVEL_MARGIN = {
    "standard": 0.12,
    "enhanced": 0.18,
    "heatwave_resilience": 0.25,
}

SOLAR_RADIATION_BY_ENVIRONMENT = {
    "mountain": 480,
    "coastal": 400,
    "rural": 420,
    "suburban": 380,
    "dense_urban": 340,
    "industrial": 360,
}


class GreencubeCoolingStudy(models.Model):
    _name = "greencube.cooling.study"
    _description = "GreenCube Cooling Study"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True, default="New study")
    reference = fields.Char(readonly=True, copy=False, index=True)
    partner_id = fields.Many2one("res.partner", tracking=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)

    state = fields.Selection(STATES, default="draft", required=True, tracking=True)
    revision_number = fields.Integer(default=1, readonly=True)
    parent_study_id = fields.Many2one("greencube.cooling.study", readonly=True, index=True)
    root_study_id = fields.Many2one("greencube.cooling.study", readonly=True, index=True)
    revision_ids = fields.One2many("greencube.cooling.study", "parent_study_id")

    thermal_specification_id = fields.Many2one("greencube.thermal.specification", tracking=True)

    address = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    country_id = fields.Many2one("res.country")
    latitude = fields.Float(digits=(10, 6))
    longitude = fields.Float(digits=(10, 6))
    altitude_m = fields.Float()
    timezone = fields.Char()
    environment_type = fields.Selection(
        [
            ("dense_urban", "Dense urban"),
            ("suburban", "Suburban"),
            ("rural", "Rural"),
            ("mountain", "Mountain"),
            ("coastal", "Coastal"),
            ("industrial", "Industrial"),
        ]
    )
    climate_confirmed = fields.Boolean(default=False)

    main_orientation = fields.Selection(
        [
            ("north", "North"),
            ("north_east", "North-East"),
            ("east", "East"),
            ("south_east", "South-East"),
            ("south", "South"),
            ("south_west", "South-West"),
            ("west", "West"),
            ("north_west", "North-West"),
        ],
        help="Compass orientation of the GreenCube's primary (front) facade. "
        "Used to rotate the four nominal facade slots (front/back/left/right) into "
        "real compass orientations on greencube.thermal.facade — stored on the study, "
        "not derived from the facades, since the rotation is otherwise not reversible "
        "(GC-COOLING-09 pt.2).",
    )

    cooling_setpoint_c = fields.Float(default=22.0)
    night_setpoint_offset_c = fields.Float(default=1.0, help="Allowed night setpoint rise above the day setpoint.")
    maximum_acceptable_temperature_c = fields.Float(
        default=25.0,
        help="Upper bound of the comfort band before it is considered breached. Previously hardcoded as "
        "cooling_setpoint_c + 2 and never settable by the user (GC-COOLING-12).",
    )
    target_humidity_percent = fields.Float(default=55.0)
    service_level = fields.Selection(
        [
            ("standard", "Confort standard"),
            ("enhanced", "Confort renforcé"),
            ("heatwave_resilience", "Résilience canicule"),
        ],
        default="standard",
        tracking=True,
    )

    @api.constrains("cooling_setpoint_c", "maximum_acceptable_temperature_c")
    def _check_comfort_temperature_band(self):
        for study in self:
            if study.maximum_acceptable_temperature_c < study.cooling_setpoint_c:
                raise ValidationError(
                    "maximum_acceptable_temperature_c must be greater than or equal to cooling_setpoint_c."
                )

    occupancy_profile_ids = fields.One2many("greencube.cooling.occupancy.profile", "study_id")
    equipment_load_ids = fields.One2many("greencube.cooling.equipment.load", "study_id")
    ventilation_profile_ids = fields.One2many("greencube.cooling.ventilation.profile", "study_id")
    shading_ids = fields.One2many("greencube.cooling.shading", "study_id")
    climate_scenario_ids = fields.One2many("greencube.cooling.climate.scenario", "study_id")
    result_ids = fields.One2many("greencube.cooling.result", "study_id")
    equipment_selection_ids = fields.One2many("greencube.cooling.equipment.selection", "study_id")
    snapshot_ids = fields.One2many("greencube.cooling.calculation.snapshot", "study_id")

    result_count = fields.Integer(compute="_compute_result_count")
    active_result_id = fields.Many2one("greencube.cooling.result", compute="_compute_active_result", store=True)
    active_snapshot_id = fields.Many2one(
        "greencube.cooling.calculation.snapshot", compute="_compute_active_snapshot", store=True
    )

    input_snapshot_json = fields.Text(readonly=True, copy=False)
    input_snapshot_hash = fields.Char(readonly=True, copy=False, index=True)
    calculation_date = fields.Datetime(readonly=True)
    validation_date = fields.Datetime(readonly=True)
    validator_id = fields.Many2one("res.users", readonly=True)
    confidence_score = fields.Float(readonly=True, digits=(4, 3))

    notes = fields.Html()

    _sql_constraints = [
        ("reference_uniq", "unique(reference)", "Reference must be unique."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("reference"):
                sequence = self.env["ir.sequence"].next_by_code("greencube.cooling.study") or "GCC/0000"
                vals["reference"] = sequence
        studies = super().create(vals_list)
        for study in studies:
            if not study.root_study_id:
                study.root_study_id = study.id
        return studies

    def _compute_result_count(self):
        for study in self:
            study.result_count = len(study.result_ids)

    def action_view_results(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Résultats",
            "res_model": "greencube.cooling.result",
            "view_mode": "list,form",
            "domain": [("study_id", "=", self.id)],
            "context": {"default_study_id": self.id},
        }

    @api.depends("result_ids", "result_ids.state")
    def _compute_active_result(self):
        for study in self:
            successful = study.result_ids.filtered(lambda r: r.state == "success").sorted("create_date", reverse=True)
            study.active_result_id = successful[:1]

    @api.depends("snapshot_ids.state")
    def _compute_active_snapshot(self):
        for study in self:
            frozen = study.snapshot_ids.filtered(lambda s: s.state == "frozen")
            study.active_snapshot_id = frozen[:1]

    LOCKED_STATES = ("validated",)

    def write(self, vals):
        blocked_fields = set(vals.keys()) - {"notes", "state", "active", "validation_date", "validator_id"}
        for study in self:
            if study.state in self.LOCKED_STATES and blocked_fields:
                raise UserError("This study is validated and locked. Create a revision to change its data.")
        return super().write(vals)

    def action_mark_ready(self):
        for study in self:
            missing = study._missing_required_sections()
            study.state = "incomplete" if missing else "ready"

    def _missing_required_sections(self):
        self.ensure_one()
        missing = []
        if not self.thermal_specification_id:
            missing.append("thermal_specification")
        # climate_confirmed, not raw lat/lon truthiness: Odoo Float fields
        # can't distinguish "never set" from "set to exactly 0.0" (e.g. the
        # equator or the Greenwich meridian), so presence must be tracked
        # via the explicit confirmation flag instead (audit GC-COOLING-03).
        if not self.climate_confirmed:
            missing.append("location")
        if not self.occupancy_profile_ids:
            missing.append("occupancy")
        return missing

    # ------------------------------------------------------------------
    # GC-COOLING-13: structured validation ("review" screen backend)
    # ------------------------------------------------------------------

    def get_validation(self):
        """Structured validation report: blocking errors, warnings, info,
        and a provenance summary across all sub-lines. This is the single
        source of truth the /validation API route and action_create_snapshot()
        both rely on — the frontend must never decide readiness on its own.
        """
        self.ensure_one()
        issues = []

        def add_issue(code, severity, section_code, title, message, blocking=False, field_path=None):
            issues.append(
                {
                    "id": f"{section_code}:{code}",
                    "code": code,
                    "severity": severity,
                    "blocking": blocking,
                    "section_code": section_code,
                    "field_path": field_path,
                    "title": title,
                    "message": message,
                }
            )

        if not self.thermal_specification_id:
            add_issue(
                "MODEL_MISSING", "error", "model", "Modèle manquant",
                "Aucune spécification thermique GreenCube n'est associée à cette étude.", blocking=True,
            )
        if not self.climate_confirmed:
            add_issue(
                "LOCATION_MISSING", "error", "location", "Localisation manquante",
                "La localisation doit être recherchée et confirmée.", blocking=True,
            )
        if not self.occupancy_profile_ids:
            add_issue(
                "OCCUPANCY_MISSING", "error", "usage", "Occupation manquante",
                "Aucun profil d'occupation n'est défini pour cette étude.", blocking=True,
            )
        if not self.ventilation_profile_ids:
            add_issue(
                "VENTILATION_MISSING", "warning", "comfort", "Ventilation non renseignée",
                "Aucun profil de ventilation défini ; les valeurs par défaut du modèle seront utilisées.",
            )
        if not self.equipment_load_ids:
            add_issue(
                "EQUIPMENT_MISSING", "info", "equipment", "Aucun équipement",
                "Aucune charge d'équipement n'est déclarée pour cette étude.",
            )

        solver = self.env["greencube.cooling.solver.version"].search(
            [("code", "=", "MERCURE"), ("state", "=", "active")], limit=1
        )
        if not solver:
            add_issue(
                "SOLVER_VERSION_MISSING", "error", "review", "Version du solver indisponible",
                "Aucune version active du solver MERCURE n'est configurée.", blocking=True,
            )

        for line in self.occupancy_profile_ids:
            if line.provenance in NON_CONFIRMED_PROVENANCES:
                add_issue(
                    "OCCUPANCY_ASSUMPTION", "warning", "usage", "Hypothèse d'occupation à confirmer",
                    f"Le profil d'occupation « {line.usage_type} » utilise une valeur {line.provenance}.",
                    field_path=f"occupancy_profile_ids/{line.id}",
                )
        for line in self.equipment_load_ids:
            if line.provenance in NON_CONFIRMED_PROVENANCES:
                add_issue(
                    "EQUIPMENT_ASSUMPTION", "warning", "equipment", "Hypothèse d'équipement à confirmer",
                    f"L'équipement « {line.name} » utilise une valeur {line.provenance}.",
                    field_path=f"equipment_load_ids/{line.id}",
                )
        for line in self.ventilation_profile_ids:
            if line.provenance in NON_CONFIRMED_PROVENANCES:
                add_issue(
                    "VENTILATION_ASSUMPTION", "warning", "comfort", "Hypothèse de ventilation à confirmer",
                    f"Le profil de ventilation utilise une valeur {line.provenance}.",
                    field_path=f"ventilation_profile_ids/{line.id}",
                )
        for line in self.shading_ids:
            if not line.confirmed:
                add_issue(
                    "SHADING_UNCONFIRMED", "warning", "orientation", "Masque solaire non confirmé",
                    f"Le masque solaire orienté {line.orientation} n'a pas été confirmé.",
                    field_path=f"shading_ids/{line.id}",
                )

        blocking_count = sum(1 for i in issues if i["blocking"])
        warning_count = sum(1 for i in issues if i["severity"] == "warning")
        info_count = sum(1 for i in issues if i["severity"] == "info")

        provenance_summary = {}
        for recordset in (
            self.occupancy_profile_ids,
            self.equipment_load_ids,
            self.ventilation_profile_ids,
            self.shading_ids,
        ):
            for line in recordset:
                provenance_summary[line.provenance] = provenance_summary.get(line.provenance, 0) + 1

        return {
            "study_id": self.id,
            "issues": issues,
            "blocking_count": blocking_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "ready": blocking_count == 0,
            "provenance_summary": provenance_summary,
            # Data completeness/provenance quality, computable before any
            # solver run — deliberately distinct from `confidence_score`,
            # which is a solver output that stays 0 until action_calculate()
            # runs (audit P1-05: Review used to show a permanent 0% before
            # the first calculation because it read the solver field).
            "completeness_score": self._compute_completeness_score(blocking_count, warning_count, provenance_summary),
            "confidence_score": self.confidence_score,
        }

    def _compute_completeness_score(self, blocking_count, warning_count, provenance_summary):
        """1.0 only when every required section is present (no blocking
        issues) and every sub-line uses a confirmed/measured/catalog
        provenance. Each remaining warning and each unconfirmed line pulls
        the score down proportionally, so a complete-but-unconfirmed study
        reads meaningfully above 0 without pretending to be solver-grade."""
        if blocking_count > 0:
            return 0.0
        total_lines = sum(provenance_summary.values())
        confirmed_lines = sum(
            count for provenance, count in provenance_summary.items() if provenance not in NON_CONFIRMED_PROVENANCES
        )
        provenance_ratio = (confirmed_lines / total_lines) if total_lines else 1.0
        score = 0.6 + 0.4 * provenance_ratio - 0.03 * warning_count
        return max(0.0, min(1.0, round(score, 3)))

    def action_confirm_assumptions(self):
        """Bulk-confirm every non-measured/non-catalog sub-line (GC-COOLING-13
        "confirmer les hypothèses non mesurées"), auditing the action on the
        study's chatter (user, date, count) rather than a bespoke audit model.
        """
        self.ensure_one()
        count = 0
        for recordset in (self.occupancy_profile_ids, self.equipment_load_ids, self.ventilation_profile_ids):
            confirmable = recordset.filtered(lambda line: line.provenance in NON_CONFIRMED_PROVENANCES)
            if confirmable:
                confirmable.write({"provenance": "user_confirmed"})
                count += len(confirmable)
        unconfirmed_shading = self.shading_ids.filtered(lambda s: not s.confirmed)
        if unconfirmed_shading:
            unconfirmed_shading.write({"confirmed": True})
            count += len(unconfirmed_shading)
        if count:
            self.message_post(body=f"{count} hypothèse(s) confirmée(s) par {self.env.user.name}.")
        return count

    def action_validate(self):
        for study in self:
            if study.state != "calculated":
                raise UserError("Only a calculated study can be validated.")
            if not self.env.user.has_group("greencube_cooling.group_greencube_cooling_technician"):
                raise UserError("Only a technician or manager can validate a study.")
            study.write(
                {
                    "state": "validated",
                    "validation_date": fields.Datetime.now(),
                    "validator_id": self.env.user.id,
                }
            )

    def action_create_revision(self):
        self.ensure_one()
        if not self.env.user.has_group("greencube_cooling.group_greencube_cooling_technician"):
            raise UserError("Only a technician or manager can create a revision.")

        copy = self.copy(
            {
                "name": self.name,
                "state": "draft",
                "parent_study_id": self.id,
                "root_study_id": self.root_study_id.id or self.id,
                "revision_number": self.revision_number + 1,
                "reference": f"{self.root_study_id.reference or self.reference}-R{self.revision_number + 1:02d}",
                "validation_date": False,
                "validator_id": False,
                "input_snapshot_json": False,
                "input_snapshot_hash": False,
                "calculation_date": False,
                "confidence_score": 0.0,
            }
        )
        for line in self.occupancy_profile_ids:
            line.copy({"study_id": copy.id})
        for line in self.equipment_load_ids:
            line.copy({"study_id": copy.id})
        for line in self.ventilation_profile_ids:
            line.copy({"study_id": copy.id})
        for line in self.shading_ids:
            line.copy({"study_id": copy.id})
        return {
            "type": "ir.actions.act_window",
            "res_model": "greencube.cooling.study",
            "res_id": copy.id,
            "view_mode": "form",
            "target": "current",
        }

    # ------------------------------------------------------------------
    # Snapshot + MERCURE
    # ------------------------------------------------------------------

    CLIMATE_SCENARIO_LABELS = {
        "reference_summer": "Été de référence",
        "hot_weather": "Forte chaleur",
        "prolonged_heatwave": "Canicule prolongée",
    }

    def _climate_scenarios_from_heuristic(self):
        """Fallback used when no coordinates are set yet or the historical
        provider is unreachable: a conservative altitude-based estimate,
        clearly weaker than real data but keeps the study calculable."""
        base_temp = 34.0 if self.altitude_m and self.altitude_m > 800 else 32.0
        peak_radiation = SOLAR_RADIATION_BY_ENVIRONMENT.get(self.environment_type, 380)
        deltas = {"reference_summer": 0, "hot_weather": 5, "prolonged_heatwave": 10}
        humidity = {"reference_summer": 45, "hot_weather": 38, "prolonged_heatwave": 30}
        wind = {"reference_summer": 2, "hot_weather": 1.5, "prolonged_heatwave": 1}
        ground = {"reference_summer": 18, "hot_weather": 19, "prolonged_heatwave": 21}
        return [
            {
                "code": code,
                "outdoor_temperature_c": base_temp + delta,
                "outdoor_relative_humidity_percent": humidity[code],
                "wind_speed_ms": wind[code],
                "ground_temperature_c": ground[code],
                "peak_radiation_wm2": peak_radiation,
                "provenance": "estimated_reference",
            }
            for code, delta in deltas.items()
        ]

    def _build_climate_scenarios(self):
        self.ensure_one()
        environment_type = self.environment_type
        scenarios = None
        if self.climate_confirmed:
            try:
                fetched = self.env["greencube.cooling.climate.dataset"].get_or_fetch_scenarios(
                    self.latitude, self.longitude, environment_type
                )
                environment_factor = SOLAR_RADIATION_BY_ENVIRONMENT.get(environment_type, 380) / 400.0
                scenarios = [
                    {
                        "code": s["code"],
                        "outdoor_temperature_c": s["outdoor_temperature_c"],
                        "outdoor_relative_humidity_percent": s["outdoor_relative_humidity_percent"],
                        "wind_speed_ms": s["wind_speed_ms"],
                        "ground_temperature_c": s["ground_temperature_c"],
                        "peak_radiation_wm2": radiation_wm2_from_daily_sum(s.get("shortwave_radiation_sum_mj_m2"))
                        * environment_factor,
                        "provenance": "api",
                        "detail": {"reference_date": s.get("reference_date"), "sample_days": fetched["sample_days"]},
                    }
                    for s in fetched["scenarios"]
                ]
            except ClimateServiceError as exc:
                _logger.warning("Historical climate lookup failed for study %s, falling back: %s", self.id, exc)

        if scenarios is None:
            scenarios = self._climate_scenarios_from_heuristic()

        self._sync_climate_scenario_records(scenarios)

        def radiation(peak):
            return {"north": peak * 0.2, "south": peak * 0.6, "east": peak * 0.75, "west": peak}

        return [
            ms.ClimateScenario(
                code=s["code"],
                label=self.CLIMATE_SCENARIO_LABELS[s["code"]],
                outdoor_temperature_c=s["outdoor_temperature_c"],
                outdoor_relative_humidity_percent=s["outdoor_relative_humidity_percent"],
                solar_radiation_by_facade_wm2=radiation(s["peak_radiation_wm2"]),
                wind_speed_ms=s["wind_speed_ms"],
                ground_temperature_c=s["ground_temperature_c"],
            )
            for s in scenarios
        ]

    def _sync_climate_scenario_records(self, scenarios):
        """Persist the scenarios used for the last calculation onto the
        study's greencube.cooling.climate.scenario child lines, so the
        provenance (real historical data vs. fallback heuristic) and the
        source values are visible/auditable instead of only living inside
        the transient MERCURE payload.

        Uses sudo(): this is an internal derived-data cache written as a
        side effect of action_calculate(), never a direct user-facing CRUD
        action (no API route exposes climate.scenario writes) — the ACL
        deliberately keeps create/write technician-only for direct access,
        but a plain "User" must still be able to run their own calculation
        (real bug found by test_http_api.py's first genuine execution:
        without sudo() here, every calculation by a non-technician user
        failed with an AccessError on this internal write).
        """
        self.ensure_one()
        existing_by_code = {rec.scenario_type: rec for rec in self.climate_scenario_ids}
        for s in scenarios:
            vals = {
                "study_id": self.id,
                "scenario_type": s["code"],
                "outdoor_temperature_c": s["outdoor_temperature_c"],
                "relative_humidity_percent": s["outdoor_relative_humidity_percent"],
                "solar_radiation_wm2": s["peak_radiation_wm2"],
                "wind_speed_ms": s["wind_speed_ms"],
                "provenance": s["provenance"],
                "detail_json": json.dumps(s.get("detail", {})),
            }
            record = existing_by_code.get(s["code"])
            if record:
                record.sudo().write(vals)
            else:
                self.env["greencube.cooling.climate.scenario"].sudo().create(vals)

    def _build_mercure_input(self):
        """Build the immutable MERCURE payload from the current study state.

        This is the GC-COOLING-13 snapshot builder in its minimal form: it
        reads the study and its sub-lines directly rather than from a
        persisted snapshot table, since climate-service and full snapshot
        persistence (GC-COOLING-03/04/13) are out of scope for this lot.
        """
        self.ensure_one()
        spec = self.thermal_specification_id
        if not spec:
            raise UserError("A GreenCube thermal specification is required before calculating.")

        wall_area = 2 * (spec.length_m + spec.width_m) * spec.height_m
        glazing_facades = []
        for facade in spec.facade_ids:
            if facade.glazing_area_m2 <= 0:
                continue
            cardinal = "north" if "north" in facade.orientation else "south" if "south" in facade.orientation else (
                "east" if facade.orientation == "east" else "west" if facade.orientation == "west" else "south"
            )
            glazing_facades.append(
                ms.GlazingFacade(
                    facade=cardinal,
                    area_m2=facade.glazing_area_m2,
                    u_value_wm2k=facade.window_u_value or 1.3,
                    solar_factor=facade.solar_factor_g or 0.5,
                    protection_factor=facade.default_shading_factor or 1.0,
                    shade_factor=1.0,
                )
            )

        occupancy = self.occupancy_profile_ids[:1]
        equipment = [
            ms.EquipmentLoad(
                id=str(line.id),
                label=line.name,
                quantity=line.quantity,
                unit_power_w=line.unit_power_w,
                load_factor=1.0,
                simultaneity_factor=line.simultaneity_percent / 100.0,
                operating_fraction=min(1.0, line.usage_hours_per_day / 24.0),
                fraction_dissipated_in_zone=line.heat_dissipation_factor,
                sensible_fraction=1.0 if line.category != "other" else 0.8,
                latent_fraction=0.0 if line.category != "other" else 0.2,
            )
            for line in self.equipment_load_ids
        ]

        ventilation = self.ventilation_profile_ids[:1]
        infiltration_ach = (ventilation.infiltration_ach if ventilation else spec.default_infiltration_ach) or 0.5

        return ms.MercureInput(
            snapshot_id=f"{self.id}-{self.revision_number}",
            snapshot_hash=self.input_snapshot_hash or "",
            study_id=str(self.id),
            study_version=str(self.revision_number),
            climate_scenarios=self._build_climate_scenarios(),
            geometry=ms.Geometry(
                length_m=spec.length_m,
                width_m=spec.width_m,
                height_m=spec.height_m,
                floor_area_m2=spec.floor_area_m2,
                volume_m3=spec.internal_volume_m3,
            ),
            envelope=ms.Envelope(
                walls=ms.EnvelopeSurface(area_m2=wall_area, u_value_wm2k=spec.wall_u_value),
                roof=ms.EnvelopeSurface(area_m2=spec.floor_area_m2, u_value_wm2k=spec.roof_u_value),
                floor=ms.EnvelopeSurface(area_m2=spec.floor_area_m2, u_value_wm2k=spec.floor_u_value),
                floor_boundary="ground",
                doors=ms.EnvelopeSurface(area_m2=2, u_value_wm2k=1.4),
                thermal_bridge_mode="percentage_adjustment",
                thermal_bridge_correction_rate=spec.thermal_bridge_factor,
            ),
            glazing=ms.Glazing(facades=glazing_facades),
            occupancy=ms.Occupancy(
                usual_occupants=occupancy.usual_occupants if occupancy else 0,
                maximum_occupants=occupancy.maximum_occupants if occupancy else 0,
                occupancy_fraction=1.0,
                sensible_gain_per_person_w=occupancy.sensible_gain_per_person_w if occupancy else 70,
                latent_gain_per_person_g_h=occupancy.latent_gain_per_person_g_h if occupancy else 50,
            ),
            equipment=equipment,
            lighting=ms.Lighting(
                mode="power_density",
                power_density_wm2=occupancy.lighting_power_density_wm2 if occupancy else 6,
                usage_fraction=occupancy.lighting_usage_fraction if occupancy else 0.6,
                fraction_dissipated_in_zone=1,
            ),
            ventilation=ms.Ventilation(
                system_type=ventilation.ventilation_type if ventilation else "simple_flow",
                airflow_m3h=ventilation.airflow_m3h if ventilation else 60,
                heat_recovery_efficiency=(ventilation.heat_recovery_efficiency_percent / 100.0) if ventilation else 0.0,
                bypass_active=ventilation.bypass_active if ventilation else False,
                fan_power_w=ventilation.fan_power_w if ventilation else 30,
                fan_fraction_dissipated_in_zone=1.0,
                fan_operating_fraction=1.0,
            ),
            infiltration=ms.Infiltration(method="n50_estimated", air_changes_per_hour=infiltration_ach),
            comfort=ms.Comfort(
                cooling_setpoint_day_c=self.cooling_setpoint_c,
                cooling_setpoint_night_c=self.cooling_setpoint_c + self.night_setpoint_offset_c,
                target_relative_humidity_percent=self.target_humidity_percent,
                maximum_acceptable_temperature_c=self.maximum_acceptable_temperature_c,
            ),
            margin_fraction=SERVICE_LEVEL_MARGIN.get(self.service_level, 0.12),
        )

    def action_create_snapshot(self, engine="quick_solver"):
        """Create an immutable greencube.cooling.calculation.snapshot record,
        freezing the current MercureInput. Re-validates via get_validation()
        (not the older _missing_required_sections()) so the same structured
        blocking rules exposed to the API are what gates snapshot creation.
        """
        self.ensure_one()
        validation = self.get_validation()
        if validation["blocking_count"]:
            blocking_messages = [issue["message"] for issue in validation["issues"] if issue["blocking"]]
            raise UserError("Cannot snapshot an incomplete or invalid study: " + "; ".join(blocking_messages))

        mercure_input = self._build_mercure_input()
        payload_dict = mercure_input_to_dict(mercure_input)
        payload_json = json.dumps(payload_dict, sort_keys=True, default=str)
        snapshot_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        # Only one frozen snapshot per study at a time: creating a new one
        # supersedes whatever was frozen before, so action_calculate() always
        # has an unambiguous "active" snapshot to source from.
        self.snapshot_ids.filtered(lambda s: s.state == "frozen").write({"state": "superseded"})
        snapshot = self.env["greencube.cooling.calculation.snapshot"].create(
            {
                "study_id": self.id,
                "study_revision_number": self.revision_number,
                "thermal_specification_id": self.thermal_specification_id.id,
                "thermal_specification_version": self.thermal_specification_id.version,
                "requested_engine": engine,
                "scenario_codes_json": json.dumps([s.code for s in mercure_input.climate_scenarios]),
                "payload_json": payload_json,
                "confirmed_assumptions_json": json.dumps(validation["provenance_summary"]),
                "snapshot_hash": snapshot_hash,
            }
        )
        # Kept in sync for backward compatibility with code/tests reading
        # these study-level fields directly; the snapshot record is the
        # actual source of truth.
        self.write({"input_snapshot_json": payload_json, "input_snapshot_hash": snapshot_hash})
        return snapshot_hash

    def action_calculate(self, engine=None, idempotency_key=None):
        """engine: None keeps the active snapshot's requested engine
        (default quick_solver); pass "quick_solver", "energyplus" or "both"
        to (re)snapshot with that choice first. Only MERCURE (quick_solver)
        actually produces the persisted numeric result today. If the
        snapshot requests energyplus/both, a real (Honeybee-shaped, tested,
        checksummed) geometry translation is attempted inline — see
        services/mercure/honeybee_translator.py — and stored as a
        simulation.artifact, but the actual EnergyPlus *simulation* is never
        run from this web request: that stays behind
        GC_COOLING_ENERGYPLUS_ENABLED and is the job of the cron-driven
        worker (GC-COOLING-15), never fabricated here.

        Every call creates a greencube.cooling.calculation.job row: this is
        what the API's job_id refers to (not a result id standing in for
        one), giving each calculation a real, queryable, serializable
        record independent of whether it produced a result.
        """
        self.ensure_one()
        if idempotency_key:
            existing = self.env["greencube.cooling.result"].search(
                [("idempotency_key", "=", idempotency_key), ("study_id", "=", self.id)], limit=1
            )
            if existing:
                return existing

        if not self.active_snapshot_id or (engine and self.active_snapshot_id.requested_engine != engine):
            self.action_create_snapshot(engine=engine or "quick_solver")

        snapshot = self.active_snapshot_id
        self.state = "calculating"
        started_at = time.monotonic()

        job = self.env["greencube.cooling.calculation.job"].create(
            {
                "study_id": self.id,
                "snapshot_id": snapshot.id,
                "requested_engine": snapshot.requested_engine,
                "status": "running",
                "started_at": fields.Datetime.now(),
                "idempotency_key": idempotency_key or None,
            }
        )

        try:
            mercure_input = mercure_input_from_dict(json.loads(snapshot.payload_json))
            result = run_mercure(mercure_input)
        except (MercureError, UserError) as exc:
            self.state = "failed"
            job.write(
                {"status": "failed", "error_message": str(exc)[:255], "finished_at": fields.Datetime.now()}
            )
            raise UserError(f"MERCURE calculation failed: {exc}") from exc

        result_state = "success"
        energyplus_warnings = []
        if snapshot.requested_engine in ("energyplus", "both"):
            energyplus_warnings, energyplus_status, result_state = self._process_energyplus_translation(
                job, mercure_input, snapshot.requested_engine, result_state
            )
            job.write({"energyplus_processing_status": energyplus_status})

        duration_ms = int((time.monotonic() - started_at) * 1000)
        solver_version = self.env["greencube.cooling.solver.version"].search(
            [("code", "=", "MERCURE"), ("state", "=", "active")], limit=1
        )
        governing = next(r for r in result.scenario_results if r.scenario_code == result.governing_scenario_code)
        commercial_tier = self.env["greencube.cooling.commercial.capacity"].find_tier_for_load_w(
            result.recommended_capacity_w
        )

        result_record = self.env["greencube.cooling.result"].create(
            {
                "study_id": self.id,
                "snapshot_id": snapshot.id,
                "solver_version_id": solver_version.id if solver_version else False,
                "state": result_state,
                "sensible_load_w": governing.sensible_load_w,
                "latent_load_w": governing.latent_load_w,
                "total_load_w": governing.total_load_w,
                "shr": governing.shr,
                "margin_w": governing.margin_w,
                "recommended_capacity_w": result.recommended_capacity_w,
                "recommended_capacity_kw": result.recommended_capacity_kw,
                "recommended_capacity_btu_h": result.recommended_capacity_btu_h,
                "commercial_capacity_id": commercial_tier.id if commercial_tier else False,
                "confidence_score": result.confidence_score,
                "governing_scenario_code": result.governing_scenario_code,
                "warnings_json": json.dumps([w.__dict__ for w in result.warnings] + energyplus_warnings),
                "main_load_drivers_json": json.dumps(result.main_load_drivers),
                "duration_ms": duration_ms,
                "snapshot_hash": snapshot.snapshot_hash,
                "idempotency_key": idempotency_key or None,
            }
        )
        for entry in governing.breakdown:
            self.env["greencube.cooling.result.component"].create(
                {
                    "result_id": result_record.id,
                    "component_code": entry.component_code,
                    "label": entry.label,
                    "sensible_w": entry.sensible_w,
                    "latent_w": entry.latent_w,
                    "total_w": entry.total_w,
                    "percentage_of_total": entry.percentage_of_total * 100,
                }
            )

        self.write(
            {
                "state": "calculated",
                "calculation_date": fields.Datetime.now(),
                "confidence_score": result.confidence_score,
            }
        )
        job.write(
            {
                "status": "completed",
                "result_id": result_record.id,
                "finished_at": fields.Datetime.now(),
                "duration_ms": duration_ms,
            }
        )
        return result_record

    def _process_energyplus_translation(self, job, mercure_input, requested_engine, result_state):
        """Attempts the (real, tested) Honeybee JSON translation inline —
        cheap, pure-Python, no subprocess. Never calls
        services.energyplus.run_energyplus_simulation: that function
        touches the actual EnergyPlus binary and is reserved for the
        standalone energyplus_worker/ process (GC-COOLING-15's isolation
        requirement), which claims jobs over HTTP and never runs inside
        this Odoo process. Returns (warnings, energyplus_processing_status, result_state)."""
        self.ensure_one()
        warnings = []
        if not is_energyplus_enabled():
            warnings.append(
                {
                    "code": "ENERGYPLUS_DISABLED",
                    "message": "EnergyPlus is disabled on this server (set GC_COOLING_ENERGYPLUS_ENABLED=true "
                    "to enable Honeybee translation).",
                    "severity": "warning",
                }
            )
            if requested_engine == "energyplus":
                result_state = "partial"
            return warnings, "disabled", result_state

        try:
            honeybee_model, diagnostics = build_honeybee_model(mercure_input)
        except HoneybeeTranslationError as exc:
            warnings.append(
                {"code": "ENERGYPLUS_TRANSLATION_FAILED", "message": str(exc), "severity": "warning"}
            )
            if requested_engine == "energyplus":
                result_state = "partial"
            return warnings, "translation_failed", result_state

        attachment = self.env["ir.attachment"].create(
            {
                "name": f"honeybee-model-job-{job.id}.json",
                "type": "binary",
                "datas": base64.b64encode(json.dumps(honeybee_model).encode("utf-8")),
                "mimetype": "application/json",
                "res_model": "greencube.cooling.calculation.job",
                "res_id": job.id,
            }
        )
        self.env["greencube.cooling.simulation.artifact"].create(
            {
                "job_id": job.id,
                "artifact_type": "honeybee_json",
                "checksum_sha256": diagnostics.checksum_sha256,
                "attachment_id": attachment.id,
            }
        )
        warnings.append(
            {
                "code": "ENERGYPLUS_QUEUED",
                "message": "Honeybee model translated and stored. The EnergyPlus simulation itself is queued "
                "for the worker (not run inline) — its outcome is not yet known.",
                "severity": "info",
            }
        )
        if requested_engine == "energyplus":
            result_state = "partial"
        return warnings, "queued_for_worker", result_state
