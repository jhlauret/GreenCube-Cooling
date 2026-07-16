# -*- coding: utf-8 -*-
import json
import time

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.mercure import schemas as ms
from ..services.mercure.engine import MercureError, run_mercure

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

    cooling_setpoint_c = fields.Float(default=25.0)
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

    occupancy_profile_ids = fields.One2many("greencube.cooling.occupancy.profile", "study_id")
    equipment_load_ids = fields.One2many("greencube.cooling.equipment.load", "study_id")
    ventilation_profile_ids = fields.One2many("greencube.cooling.ventilation.profile", "study_id")
    shading_ids = fields.One2many("greencube.cooling.shading", "study_id")
    climate_scenario_ids = fields.One2many("greencube.cooling.climate.scenario", "study_id")
    result_ids = fields.One2many("greencube.cooling.result", "study_id")
    equipment_selection_ids = fields.One2many("greencube.cooling.equipment.selection", "study_id")

    result_count = fields.Integer(compute="_compute_result_count")
    active_result_id = fields.Many2one("greencube.cooling.result", compute="_compute_active_result", store=True)

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
        if not self.latitude or not self.longitude:
            missing.append("location")
        if not self.occupancy_profile_ids:
            missing.append("occupancy")
        return missing

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

    def _build_climate_scenarios(self):
        self.ensure_one()
        base_temp = 34.0 if self.altitude_m and self.altitude_m > 800 else 32.0
        peak_radiation = SOLAR_RADIATION_BY_ENVIRONMENT.get(self.environment_type, 380)

        def radiation(peak):
            return {"north": peak * 0.2, "south": peak * 0.6, "east": peak * 0.75, "west": peak}

        return [
            ms.ClimateScenario(
                code="reference_summer",
                label="Été de référence",
                outdoor_temperature_c=base_temp,
                outdoor_relative_humidity_percent=45,
                solar_radiation_by_facade_wm2=radiation(peak_radiation),
                wind_speed_ms=2,
                ground_temperature_c=18,
            ),
            ms.ClimateScenario(
                code="hot_weather",
                label="Forte chaleur",
                outdoor_temperature_c=base_temp + 5,
                outdoor_relative_humidity_percent=38,
                solar_radiation_by_facade_wm2=radiation(peak_radiation),
                wind_speed_ms=1.5,
                ground_temperature_c=19,
            ),
            ms.ClimateScenario(
                code="prolonged_heatwave",
                label="Canicule prolongée",
                outdoor_temperature_c=base_temp + 10,
                outdoor_relative_humidity_percent=30,
                solar_radiation_by_facade_wm2=radiation(peak_radiation),
                wind_speed_ms=1,
                ground_temperature_c=21,
            ),
        ]

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
            lighting=ms.Lighting(mode="power_density", power_density_wm2=6, usage_fraction=0.6, fraction_dissipated_in_zone=1),
            ventilation=ms.Ventilation(
                system_type=ventilation.ventilation_type if ventilation else "simple_flow",
                airflow_m3h=ventilation.airflow_m3h if ventilation else 60,
                heat_recovery_efficiency=(ventilation.heat_recovery_efficiency_percent / 100.0) if ventilation else 0.0,
                bypass_active=False,
                fan_power_w=30,
                fan_fraction_dissipated_in_zone=1.0,
                fan_operating_fraction=1.0,
            ),
            infiltration=ms.Infiltration(method="n50_estimated", air_changes_per_hour=infiltration_ach),
            comfort=ms.Comfort(
                cooling_setpoint_day_c=self.cooling_setpoint_c,
                cooling_setpoint_night_c=self.cooling_setpoint_c + 1,
                target_relative_humidity_percent=self.target_humidity_percent,
                maximum_acceptable_temperature_c=self.cooling_setpoint_c + 2,
            ),
            margin_fraction=SERVICE_LEVEL_MARGIN.get(self.service_level, 0.12),
        )

    def action_create_snapshot(self):
        self.ensure_one()
        missing = self._missing_required_sections()
        if missing:
            raise UserError(f"Cannot snapshot an incomplete study. Missing: {', '.join(missing)}")

        mercure_input = self._build_mercure_input()
        payload = {
            "study_id": self.id,
            "revision": self.revision_number,
            "company_id": self.company_id.id,
            "user_id": self.env.user.id,
            "date": fields.Datetime.now().isoformat(),
            "thermal_specification": {
                "id": self.thermal_specification_id.id,
                "version": self.thermal_specification_id.version,
            },
        }
        snapshot_hash = str(abs(hash(json.dumps(payload, sort_keys=True, default=str))))
        self.write({"input_snapshot_json": json.dumps(payload, default=str), "input_snapshot_hash": snapshot_hash})
        return snapshot_hash

    def action_calculate(self):
        self.ensure_one()
        if not self.input_snapshot_hash:
            self.action_create_snapshot()

        self.state = "calculating"
        started_at = time.monotonic()
        try:
            mercure_input = self._build_mercure_input()
            result = run_mercure(mercure_input)
        except (MercureError, UserError) as exc:
            self.state = "failed"
            raise UserError(f"MERCURE calculation failed: {exc}") from exc

        duration_ms = int((time.monotonic() - started_at) * 1000)
        solver_version = self.env["greencube.cooling.solver.version"].search(
            [("code", "=", "MERCURE"), ("state", "=", "active")], limit=1
        )
        governing = next(r for r in result.scenario_results if r.scenario_code == result.governing_scenario_code)

        result_record = self.env["greencube.cooling.result"].create(
            {
                "study_id": self.id,
                "solver_version_id": solver_version.id if solver_version else False,
                "state": "success",
                "sensible_load_w": governing.sensible_load_w,
                "latent_load_w": governing.latent_load_w,
                "total_load_w": governing.total_load_w,
                "shr": governing.shr,
                "margin_w": governing.margin_w,
                "recommended_capacity_w": result.recommended_capacity_w,
                "recommended_capacity_kw": result.recommended_capacity_kw,
                "recommended_capacity_btu_h": result.recommended_capacity_btu_h,
                "confidence_score": result.confidence_score,
                "governing_scenario_code": result.governing_scenario_code,
                "warnings_json": json.dumps([w.__dict__ for w in result.warnings]),
                "main_load_drivers_json": json.dumps(result.main_load_drivers),
                "duration_ms": duration_ms,
                "snapshot_hash": self.input_snapshot_hash,
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
        return result_record
