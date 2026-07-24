# -*- coding: utf-8 -*-
from odoo import fields, models


class GreencubeCoolingClimateScenario(models.Model):
    _name = "greencube.cooling.climate.scenario"
    _description = "GreenCube Cooling Climate Scenario"
    _sql_constraints = [
        ("study_scenario_uniq", "unique(study_id, scenario_type)", "A scenario type can only appear once per study."),
    ]

    study_id = fields.Many2one("greencube.cooling.study", required=True, ondelete="cascade", index=True)
    scenario_type = fields.Selection(
        [
            ("reference_summer", "Été de référence"),
            ("hot_weather", "Forte chaleur"),
            ("prolonged_heatwave", "Canicule prolongée"),
        ],
        required=True,
    )
    outdoor_temperature_c = fields.Float()
    night_temperature_c = fields.Float()
    relative_humidity_percent = fields.Float()
    solar_radiation_wm2 = fields.Float()
    wind_speed_ms = fields.Float()
    duration_hours = fields.Float()
    confidence_score = fields.Float(digits=(4, 3))
    # --- Provenance / governance (GC-COOLING-04) ---------------------------
    # Links the last-computed scenario back to the exact immutable dataset
    # row it was derived from (when derived from real historical data;
    # left empty for the altitude-based fallback heuristic, which has no
    # backing dataset at all). `dataset_type`/`checksum` are denormalized
    # copies of the dataset's own fields at the time this scenario was
    # written, so they remain readable even if the dataset is later
    # superseded by a fresh fetch.
    dataset_id = fields.Many2one("greencube.cooling.climate.dataset", ondelete="set null", index=True)
    dataset_type = fields.Selection(
        [
            ("historical_observed", "Historique observé"),
            ("typical_year", "Année type"),
            ("design_day", "Jour de dimensionnement"),
            ("extreme_event", "Événement extrême"),
            ("projection", "Projection"),
        ],
        help="Empty when this scenario comes from the altitude-based fallback heuristic, not a real dataset.",
    )
    checksum = fields.Char(help="Copy of the source dataset's checksum at the time this scenario was computed.")
    provenance = fields.Selection(
        [
            ("catalog", "Catalog"),
            ("api", "API"),
            ("user_confirmed", "User confirmed"),
            ("estimated_reference", "Estimated (reference)"),
            ("estimated_manual", "Estimated (manual)"),
            ("missing_fallback", "Missing (fallback)"),
        ],
        default="estimated_reference",
    )
    detail_json = fields.Text()
