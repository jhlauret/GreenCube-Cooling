# -*- coding: utf-8 -*-
"""Immutable input/output schemas for MERCURE. No Odoo ORM dependency.

Mirrors frontend/src/mercure/types.ts so the same snapshot shape can be
produced by the frontend mock and by Odoo once the real snapshot builder
(GC-COOLING-13) is wired in.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

ScenarioCode = Literal["reference_summer", "hot_weather", "prolonged_heatwave"]
Facade = Literal["north", "south", "east", "west"]
FloorBoundary = Literal["ground", "outdoor_air", "unconditioned_space", "conditioned_space", "unknown"]
ThermalBridgeMode = Literal["percentage_adjustment", "explicit_linear", "global_default", "none"]


@dataclass(frozen=True)
class ClimateScenario:
    code: ScenarioCode
    label: str
    outdoor_temperature_c: float
    outdoor_relative_humidity_percent: float
    solar_radiation_by_facade_wm2: Dict[str, float]
    wind_speed_ms: float
    ground_temperature_c: float


@dataclass(frozen=True)
class EnvelopeSurface:
    area_m2: float
    u_value_wm2k: float


@dataclass(frozen=True)
class Geometry:
    length_m: float
    width_m: float
    height_m: float
    floor_area_m2: float
    volume_m3: float


@dataclass(frozen=True)
class Envelope:
    walls: EnvelopeSurface
    roof: EnvelopeSurface
    floor: EnvelopeSurface
    floor_boundary: FloorBoundary
    doors: EnvelopeSurface
    thermal_bridge_mode: ThermalBridgeMode
    thermal_bridge_correction_rate: float


@dataclass(frozen=True)
class GlazingFacade:
    facade: Facade
    area_m2: float
    u_value_wm2k: float
    solar_factor: float
    protection_factor: float
    shade_factor: float


@dataclass(frozen=True)
class Glazing:
    facades: List[GlazingFacade]


@dataclass(frozen=True)
class Occupancy:
    usual_occupants: float
    maximum_occupants: float
    occupancy_fraction: float
    sensible_gain_per_person_w: float
    latent_gain_per_person_g_h: float


@dataclass(frozen=True)
class EquipmentLoad:
    id: str
    label: str
    quantity: float
    unit_power_w: float
    load_factor: float
    simultaneity_factor: float
    operating_fraction: float
    fraction_dissipated_in_zone: float
    sensible_fraction: float
    latent_fraction: float


@dataclass(frozen=True)
class Lighting:
    mode: Literal["power_density", "fixtures"]
    power_density_wm2: float
    usage_fraction: float
    fraction_dissipated_in_zone: float


@dataclass(frozen=True)
class Ventilation:
    system_type: Literal["natural", "simple_flow", "double_flow", "dedicated_mechanical"]
    airflow_m3h: float
    heat_recovery_efficiency: float
    bypass_active: bool
    fan_power_w: float
    fan_fraction_dissipated_in_zone: float
    fan_operating_fraction: float


@dataclass(frozen=True)
class Infiltration:
    method: Literal["ach", "n50_estimated"]
    air_changes_per_hour: float


@dataclass(frozen=True)
class Comfort:
    cooling_setpoint_day_c: float
    cooling_setpoint_night_c: float
    target_relative_humidity_percent: float
    maximum_acceptable_temperature_c: float


@dataclass(frozen=True)
class MercureInput:
    snapshot_id: str
    snapshot_hash: str
    study_id: str
    study_version: str
    climate_scenarios: List[ClimateScenario]
    geometry: Geometry
    envelope: Envelope
    glazing: Glazing
    occupancy: Occupancy
    equipment: List[EquipmentLoad]
    lighting: Lighting
    ventilation: Ventilation
    infiltration: Infiltration
    comfort: Comfort
    margin_fraction: float


@dataclass
class ComponentBreakdownEntry:
    component_code: str
    label: str
    sensible_w: float
    latent_w: float
    total_w: float = 0.0
    percentage_of_total: float = 0.0


@dataclass(frozen=True)
class MercureWarning:
    code: str
    level: Literal["info", "warning", "error"]
    message: str
    component: Optional[str] = None


@dataclass
class MercureScenarioResult:
    scenario_code: ScenarioCode
    sensible_load_w: float
    latent_load_w: float
    total_load_w: float
    shr: float
    margin_w: float
    recommended_load_w: float
    breakdown: List[ComponentBreakdownEntry]
    warnings: List[MercureWarning]
    confidence_score: float


@dataclass
class MercureResult:
    engine_code: str
    engine_version: str
    snapshot_id: str
    snapshot_hash: str
    scenario_results: List[MercureScenarioResult]
    governing_scenario_code: ScenarioCode
    recommended_capacity_w: float
    recommended_capacity_kw: float
    recommended_capacity_btu_h: float
    confidence_score: float
    main_load_drivers: List[str]
    warnings: List[MercureWarning] = field(default_factory=list)
