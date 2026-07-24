# -*- coding: utf-8 -*-
"""MERCURE — fast cooling-load pre-dimensioning engine.

Pure functions only: no ORM access, no current-time reads, no mutation of
inputs. Ports frontend/src/mercure/engine.ts 1:1 so both implementations
can be validated against the same reference cases
(see README_GC-COOLING-14_MERCURE.md).
"""
from typing import List

from .constants import (
    AIR_DENSITY,
    AIR_SPECIFIC_HEAT,
    LATENT_HEAT_OF_VAPORIZATION,
    MERCURE_ENGINE_CODE,
    MERCURE_ENGINE_VERSION,
)
from .conversions import (
    ach_to_m3h,
    humidity_ratio_from_temperature_rh,
    m3h_to_m3s,
    positive_cooling_delta_t,
    watts_to_btu_per_hour,
    watts_to_kw,
)
from .schemas import (
    ClimateScenario,
    ComponentBreakdownEntry,
    FacadeSolarGain,
    MercureInput,
    MercureResult,
    MercureScenarioResult,
    MercureWarning,
)


class MercureError(Exception):
    """Raised with a structured error code per README_GC-COOLING-14_MERCURE.md."""


def _transmission_loads(mercure_input: MercureInput, delta_t: float) -> List[ComponentBreakdownEntry]:
    envelope = mercure_input.envelope
    entries = [
        ComponentBreakdownEntry(
            component_code="envelope_walls",
            label="Murs",
            sensible_w=envelope.walls.u_value_wm2k * envelope.walls.area_m2 * delta_t,
            latent_w=0.0,
        ),
        ComponentBreakdownEntry(
            component_code="envelope_roof",
            label="Toiture",
            sensible_w=envelope.roof.u_value_wm2k * envelope.roof.area_m2 * delta_t,
            latent_w=0.0,
        ),
        ComponentBreakdownEntry(
            component_code="envelope_doors",
            label="Portes",
            sensible_w=envelope.doors.u_value_wm2k * envelope.doors.area_m2 * delta_t,
            latent_w=0.0,
        ),
    ]

    floor_delta_t = delta_t * 0.3 if envelope.floor_boundary == "ground" else delta_t
    floor_active = envelope.floor_boundary != "conditioned_space"
    entries.append(
        ComponentBreakdownEntry(
            component_code="envelope_floor",
            label="Plancher",
            sensible_w=(envelope.floor.u_value_wm2k * envelope.floor.area_m2 * floor_delta_t) if floor_active else 0.0,
            latent_w=0.0,
        )
    )

    glazing_conduction = sum(f.u_value_wm2k * f.area_m2 * delta_t for f in mercure_input.glazing.facades)
    entries.append(
        ComponentBreakdownEntry(
            component_code="glazing_conduction",
            label="Vitrages (conduction)",
            sensible_w=glazing_conduction,
            latent_w=0.0,
        )
    )

    envelope_total = sum(e.sensible_w for e in entries)
    thermal_bridge_w = 0.0
    if envelope.thermal_bridge_mode == "percentage_adjustment":
        thermal_bridge_w = envelope_total * envelope.thermal_bridge_correction_rate
    entries.append(
        ComponentBreakdownEntry(component_code="thermal_bridges", label="Ponts thermiques", sensible_w=thermal_bridge_w, latent_w=0.0)
    )

    for e in entries:
        e.total_w = e.sensible_w + e.latent_w
    return entries


def _solar_glazing_gain(
    mercure_input: MercureInput, scenario: ClimateScenario
) -> "tuple[ComponentBreakdownEntry, list]":
    total_w = 0.0
    by_facade = []
    for f in mercure_input.glazing.facades:
        radiation = scenario.solar_radiation_by_facade_wm2.get(f.facade, 0.0)
        gain_w = f.area_m2 * radiation * f.solar_factor * f.protection_factor * f.shade_factor
        total_w += gain_w
        by_facade.append(
            FacadeSolarGain(
                facade=f.facade,
                area_m2=f.area_m2,
                radiation_wm2=radiation,
                solar_factor=f.solar_factor,
                protection_factor=f.protection_factor,
                gain_w=gain_w,
            )
        )
    entry = ComponentBreakdownEntry(
        component_code="solar_glazing", label="Apports solaires vitrages", sensible_w=total_w, latent_w=0.0, total_w=total_w
    )
    return entry, by_facade


def _occupancy_gains(mercure_input: MercureInput):
    occupancy = mercure_input.occupancy
    effective = occupancy.usual_occupants * occupancy.occupancy_fraction
    sensible_w = effective * occupancy.sensible_gain_per_person_w
    latent_w = effective * occupancy.latent_gain_per_person_g_h * (LATENT_HEAT_OF_VAPORIZATION.value / 1000.0) / 3600.0
    sensible = ComponentBreakdownEntry(component_code="occupants_sensible", label="Occupants sensible", sensible_w=sensible_w, latent_w=0.0, total_w=sensible_w)
    latent = ComponentBreakdownEntry(component_code="occupants_latent", label="Occupants latent", sensible_w=0.0, latent_w=latent_w, total_w=latent_w)
    return sensible, latent


def _equipment_gains(mercure_input: MercureInput):
    sensible_w = 0.0
    latent_w = 0.0
    for eq in mercure_input.equipment:
        active_power = eq.quantity * eq.unit_power_w * eq.load_factor * eq.simultaneity_factor * eq.operating_fraction
        zone_heat = active_power * eq.fraction_dissipated_in_zone
        sensible_w += zone_heat * eq.sensible_fraction
        latent_w += zone_heat * eq.latent_fraction
    sensible = ComponentBreakdownEntry(component_code="equipment_sensible", label="Équipements sensible", sensible_w=sensible_w, latent_w=0.0, total_w=sensible_w)
    latent = ComponentBreakdownEntry(component_code="equipment_latent", label="Équipements latent", sensible_w=0.0, latent_w=latent_w, total_w=latent_w)
    return sensible, latent


def _lighting_gain(mercure_input: MercureInput) -> ComponentBreakdownEntry:
    lighting = mercure_input.lighting
    geometry = mercure_input.geometry
    sensible_w = geometry.floor_area_m2 * lighting.power_density_wm2 * lighting.usage_fraction * lighting.fraction_dissipated_in_zone
    return ComponentBreakdownEntry(component_code="lighting", label="Éclairage", sensible_w=sensible_w, latent_w=0.0, total_w=sensible_w)


def _fan_heat_gain(mercure_input: MercureInput) -> ComponentBreakdownEntry:
    ventilation = mercure_input.ventilation
    sensible_w = ventilation.fan_power_w * ventilation.fan_fraction_dissipated_in_zone * ventilation.fan_operating_fraction
    return ComponentBreakdownEntry(component_code="fan_heat", label="Chaleur ventilateurs", sensible_w=sensible_w, latent_w=0.0, total_w=sensible_w)


def _ventilation_loads(mercure_input: MercureInput, scenario: ClimateScenario, delta_t: float):
    ventilation = mercure_input.ventilation
    comfort = mercure_input.comfort
    flow_m3s = m3h_to_m3s(ventilation.airflow_m3h)
    recovery_efficiency = 0.0 if ventilation.bypass_active else ventilation.heat_recovery_efficiency
    non_recovered_factor = 1.0 - recovery_efficiency

    sensible_w = AIR_DENSITY.value * AIR_SPECIFIC_HEAT.value * flow_m3s * delta_t * non_recovered_factor

    outdoor_humidity_ratio = humidity_ratio_from_temperature_rh(scenario.outdoor_temperature_c, scenario.outdoor_relative_humidity_percent)
    indoor_humidity_ratio = humidity_ratio_from_temperature_rh(comfort.cooling_setpoint_day_c, comfort.target_relative_humidity_percent)
    humidity_ratio_delta = max(0.0, outdoor_humidity_ratio - indoor_humidity_ratio)
    mass_flow_kgs = flow_m3s * AIR_DENSITY.value
    latent_w = mass_flow_kgs * humidity_ratio_delta * LATENT_HEAT_OF_VAPORIZATION.value * non_recovered_factor

    sensible = ComponentBreakdownEntry(component_code="ventilation_sensible", label="Ventilation sensible", sensible_w=sensible_w, latent_w=0.0, total_w=sensible_w)
    latent = ComponentBreakdownEntry(component_code="ventilation_latent", label="Ventilation latente", sensible_w=0.0, latent_w=latent_w, total_w=latent_w)
    return sensible, latent


def _infiltration_loads(mercure_input: MercureInput, scenario: ClimateScenario, delta_t: float):
    infiltration = mercure_input.infiltration
    geometry = mercure_input.geometry
    comfort = mercure_input.comfort
    flow_m3h = ach_to_m3h(infiltration.air_changes_per_hour, geometry.volume_m3)
    flow_m3s = m3h_to_m3s(flow_m3h)
    sensible_w = AIR_DENSITY.value * AIR_SPECIFIC_HEAT.value * flow_m3s * delta_t

    outdoor_humidity_ratio = humidity_ratio_from_temperature_rh(scenario.outdoor_temperature_c, scenario.outdoor_relative_humidity_percent)
    indoor_humidity_ratio = humidity_ratio_from_temperature_rh(comfort.cooling_setpoint_day_c, comfort.target_relative_humidity_percent)
    humidity_ratio_delta = max(0.0, outdoor_humidity_ratio - indoor_humidity_ratio)
    mass_flow_kgs = flow_m3s * AIR_DENSITY.value
    latent_w = mass_flow_kgs * humidity_ratio_delta * LATENT_HEAT_OF_VAPORIZATION.value

    sensible = ComponentBreakdownEntry(component_code="infiltration_sensible", label="Infiltration sensible", sensible_w=sensible_w, latent_w=0.0, total_w=sensible_w)
    latent = ComponentBreakdownEntry(component_code="infiltration_latent", label="Infiltration latente", sensible_w=0.0, latent_w=latent_w, total_w=latent_w)
    return sensible, latent


def _compute_confidence_score(mercure_input: MercureInput, warnings: List[MercureWarning]) -> float:
    score = 1.0
    if mercure_input.infiltration.method == "n50_estimated":
        score -= 0.15
    if mercure_input.envelope.floor_boundary == "unknown":
        score -= 0.1
    if mercure_input.envelope.floor_boundary == "ground":
        score -= 0.05
    score -= sum(1 for w in warnings if w.level == "warning") * 0.05
    return max(0.0, min(1.0, score))


def _build_warnings(mercure_input: MercureInput, glazing_ratio: float) -> List[MercureWarning]:
    warnings: List[MercureWarning] = []
    if mercure_input.infiltration.method == "n50_estimated":
        warnings.append(
            MercureWarning(
                code="LOW_CONFIDENCE_INFILTRATION",
                level="warning",
                message="L'infiltration est estimée à partir d'une valeur n50, sans méthode de conversion mesurée.",
                component="infiltration",
            )
        )
    if mercure_input.envelope.floor_boundary in ("ground", "unknown"):
        warnings.append(
            MercureWarning(
                code="MISSING_GROUND_TEMPERATURE",
                level="info",
                message="La température de sol est une hypothèse par défaut.",
                component="envelope_floor",
            )
        )
    if glazing_ratio > 0.4:
        warnings.append(
            MercureWarning(
                code="HIGH_GLAZING_RATIO",
                level="warning",
                message="La surface vitrée dépasse 40 % de la surface au sol : vérifier les protections solaires.",
                component="glazing",
            )
        )
    return warnings


def _compute_scenario_result(mercure_input: MercureInput, scenario: ClimateScenario) -> MercureScenarioResult:
    delta_t = positive_cooling_delta_t(scenario.outdoor_temperature_c, mercure_input.comfort.cooling_setpoint_day_c)

    transmission = _transmission_loads(mercure_input, delta_t)
    solar, solar_gain_by_facade = _solar_glazing_gain(mercure_input, scenario)
    occ_sensible, occ_latent = _occupancy_gains(mercure_input)
    eq_sensible, eq_latent = _equipment_gains(mercure_input)
    lighting = _lighting_gain(mercure_input)
    fan = _fan_heat_gain(mercure_input)
    vent_sensible, vent_latent = _ventilation_loads(mercure_input, scenario, delta_t)
    infil_sensible, infil_latent = _infiltration_loads(mercure_input, scenario, delta_t)

    breakdown = [
        *transmission,
        solar,
        occ_sensible,
        occ_latent,
        eq_sensible,
        eq_latent,
        lighting,
        fan,
        vent_sensible,
        vent_latent,
        infil_sensible,
        infil_latent,
    ]

    sensible_load_w = sum(e.sensible_w for e in breakdown)
    latent_load_w = sum(e.latent_w for e in breakdown)
    total_load_w = sensible_load_w + latent_load_w
    shr = (sensible_load_w / total_load_w) if total_load_w > 0 else 1.0

    glazing_area = sum(f.area_m2 for f in mercure_input.glazing.facades)
    glazing_ratio = (glazing_area / mercure_input.geometry.floor_area_m2) if mercure_input.geometry.floor_area_m2 > 0 else 0.0
    warnings = _build_warnings(mercure_input, glazing_ratio)

    margin_w = total_load_w * mercure_input.margin_fraction
    recommended_load_w = total_load_w + margin_w

    for e in breakdown:
        e.percentage_of_total = (e.total_w / total_load_w) if total_load_w > 0 else 0.0

    return MercureScenarioResult(
        scenario_code=scenario.code,
        sensible_load_w=sensible_load_w,
        latent_load_w=latent_load_w,
        total_load_w=total_load_w,
        shr=shr,
        margin_w=margin_w,
        recommended_load_w=recommended_load_w,
        breakdown=breakdown,
        warnings=warnings,
        confidence_score=_compute_confidence_score(mercure_input, warnings),
        solar_gain_by_facade=solar_gain_by_facade,
    )


def select_governing_scenario(results: List[MercureScenarioResult]) -> MercureScenarioResult:
    return max(results, key=lambda r: r.recommended_load_w)


def identify_main_load_drivers(result: MercureScenarioResult, top_n: int = 3) -> List[str]:
    ranked = sorted(result.breakdown, key=lambda e: e.total_w, reverse=True)
    return [e.label for e in ranked[:top_n]]


def run_mercure(mercure_input: MercureInput) -> MercureResult:
    if len(mercure_input.climate_scenarios) == 0:
        raise MercureError("MISSING_CLIMATE_SCENARIO")
    if mercure_input.geometry.floor_area_m2 <= 0 or mercure_input.geometry.volume_m3 <= 0:
        raise MercureError("INVALID_GEOMETRY")

    scenario_results = [_compute_scenario_result(mercure_input, s) for s in mercure_input.climate_scenarios]
    governing = select_governing_scenario(scenario_results)
    all_warnings = [w for r in scenario_results for w in r.warnings]
    overall_confidence = sum(r.confidence_score for r in scenario_results) / len(scenario_results)

    return MercureResult(
        engine_code=MERCURE_ENGINE_CODE,
        engine_version=MERCURE_ENGINE_VERSION,
        snapshot_id=mercure_input.snapshot_id,
        snapshot_hash=mercure_input.snapshot_hash,
        scenario_results=scenario_results,
        governing_scenario_code=governing.scenario_code,
        recommended_capacity_w=governing.recommended_load_w,
        recommended_capacity_kw=watts_to_kw(governing.recommended_load_w),
        recommended_capacity_btu_h=watts_to_btu_per_hour(governing.recommended_load_w),
        confidence_score=overall_confidence,
        main_load_drivers=identify_main_load_drivers(governing),
        warnings=all_warnings,
    )
