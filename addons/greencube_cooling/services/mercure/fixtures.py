# -*- coding: utf-8 -*-
"""Reference cases for MERCURE, mirroring frontend/src/mercure/fixtures.ts."""
import dataclasses

from .schemas import (
    Comfort,
    Envelope,
    EnvelopeSurface,
    EquipmentLoad,
    Geometry,
    Glazing,
    GlazingFacade,
    Infiltration,
    Lighting,
    MercureInput,
    Occupancy,
    Ventilation,
)


def reference_scenario():
    from .schemas import ClimateScenario

    return ClimateScenario(
        code="reference_summer",
        label="Été de référence",
        outdoor_temperature_c=32,
        outdoor_relative_humidity_percent=45,
        solar_radiation_by_facade_wm2={"north": 80, "south": 350, "east": 200, "west": 420},
        wind_speed_ms=2,
        ground_temperature_c=18,
    )


def hot_weather_scenario():
    base = reference_scenario()
    return dataclasses.replace(base, code="hot_weather", label="Forte chaleur", outdoor_temperature_c=37, outdoor_relative_humidity_percent=35)


def heatwave_scenario():
    base = reference_scenario()
    return dataclasses.replace(base, code="prolonged_heatwave", label="Canicule prolongée", outdoor_temperature_c=42, outdoor_relative_humidity_percent=30)


def studio_standard_input() -> MercureInput:
    """Studio standard — 30 m2, 2 occupants, vitrage modéré, faible charge interne."""
    return MercureInput(
        snapshot_id="fixture-studio",
        snapshot_hash="hash-studio",
        study_id="study-fixture",
        study_version="1",
        climate_scenarios=[reference_scenario(), hot_weather_scenario(), heatwave_scenario()],
        geometry=Geometry(length_m=6, width_m=5, height_m=2.6, floor_area_m2=30, volume_m3=78),
        envelope=Envelope(
            walls=EnvelopeSurface(area_m2=45, u_value_wm2k=0.22),
            roof=EnvelopeSurface(area_m2=30, u_value_wm2k=0.18),
            floor=EnvelopeSurface(area_m2=30, u_value_wm2k=0.25),
            floor_boundary="ground",
            doors=EnvelopeSurface(area_m2=2, u_value_wm2k=1.4),
            thermal_bridge_mode="percentage_adjustment",
            thermal_bridge_correction_rate=0.05,
        ),
        glazing=Glazing(facades=[GlazingFacade(facade="south", area_m2=4, u_value_wm2k=1.3, solar_factor=0.5, protection_factor=0.7, shade_factor=1)]),
        occupancy=Occupancy(usual_occupants=2, maximum_occupants=3, occupancy_fraction=1, sensible_gain_per_person_w=70, latent_gain_per_person_g_h=50),
        equipment=[
            EquipmentLoad(
                id="laptop",
                label="Ordinateur portable",
                quantity=1,
                unit_power_w=45,
                load_factor=1,
                simultaneity_factor=1,
                operating_fraction=1,
                fraction_dissipated_in_zone=1,
                sensible_fraction=1,
                latent_fraction=0,
            )
        ],
        lighting=Lighting(mode="power_density", power_density_wm2=6, usage_fraction=0.6, fraction_dissipated_in_zone=1),
        ventilation=Ventilation(
            system_type="simple_flow",
            airflow_m3h=60,
            heat_recovery_efficiency=0,
            bypass_active=False,
            fan_power_w=30,
            fan_fraction_dissipated_in_zone=1,
            fan_operating_fraction=1,
        ),
        infiltration=Infiltration(method="ach", air_changes_per_hour=0.6),
        comfort=Comfort(cooling_setpoint_day_c=25, cooling_setpoint_night_c=26, target_relative_humidity_percent=50, maximum_acceptable_temperature_c=27),
        margin_fraction=0.15,
    )


def west_glazed_office_input() -> MercureInput:
    """Bureau fortement vitré à l'ouest — sans protection."""
    base = studio_standard_input()
    return dataclasses.replace(
        base,
        snapshot_id="fixture-west-office",
        occupancy=dataclasses.replace(base.occupancy, usual_occupants=4, maximum_occupants=6),
        glazing=Glazing(facades=[GlazingFacade(facade="west", area_m2=10, u_value_wm2k=1.3, solar_factor=0.6, protection_factor=1, shade_factor=1)]),
        equipment=[
            *base.equipment,
            EquipmentLoad(
                id="monitor",
                label="Écrans",
                quantity=4,
                unit_power_w=30,
                load_factor=1,
                simultaneity_factor=1,
                operating_fraction=1,
                fraction_dissipated_in_zone=1,
                sensible_fraction=1,
                latent_fraction=0,
            ),
        ],
    )
