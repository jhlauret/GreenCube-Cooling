# -*- coding: utf-8 -*-
"""Pure, ORM-independent MercureInput -> Honeybee-shaped model translator
(GC-COOLING-05A). Deliberately mirrors the "MERCURE stays independent of
the ORM" pattern of engine.py/serialization.py in this same package: no
Odoo import here, so it can be unit-tested without a running Odoo instance.

Scope: build a deterministic, checksummed JSON export of a snapshot's
geometry/envelope/glazing/occupancy/equipment/lighting/ventilation, shaped
after Honeybee's Model/Room/Face schema closely enough to be a real
starting point for an actual honeybee-energy translation, WITHOUT
depending on the honeybee-energy/honeybee-schema packages (not installed
in this environment — see services/energyplus.py's availability check).
It does not run any simulation and never will from this module: EnergyPlus
execution belongs in the worker (services/energyplus.py + the
calculation.job cron), never inline here.

This module does NOT claim schema-exact parity with honeybee-schema's
Model.to_dict() — it is a simplified, clearly-documented approximation
(see BuildDiagnostics.assumptions on every call). A full binary-compatible
Honeybee model would need the actual honeybee-energy library to construct
Room/Face/Aperture/Construction objects and call their own .to_dict().
"""
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List

from .schemas import MercureInput


class HoneybeeTranslationError(Exception):
    """Raised when the snapshot's geometry/envelope is too incomplete or
    physically inconsistent to translate (e.g. a non-positive dimension) —
    distinct from EnergyPlusUnavailableError/EnergyPlusSimulationError in
    services/energyplus.py, which are about the *simulation* stack, not the
    translation input."""


@dataclass
class BuildDiagnostics:
    assumptions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checksum_sha256: str = ""

    def to_dict(self) -> Dict:
        return {"assumptions": self.assumptions, "warnings": self.warnings, "checksum_sha256": self.checksum_sha256}


# Front/back facades (north/south-labelled) are assumed to span the
# building's width; side facades (east/west) span its length — the same
# box-footprint convention frontend/src/sync/syncStudy.ts's
# facadeGrossAreaM2() and cooling_study.py's wall_area estimate use, so the
# translator's geometry stays consistent with what the rest of the system
# already assumes about a GreenCube's shape.
_WIDTH_FACADES = {"north", "south"}


def _wall_face(facade: str, length_m: float, width_m: float, height_m: float, wall_u: float) -> Dict:
    gross_area = (width_m if facade in _WIDTH_FACADES else length_m) * height_m
    return {
        "type": "Face",
        "identifier": f"wall-{facade}",
        "face_type": "Wall",
        "boundary_condition": "Outdoors",
        "azimuth_label": facade,
        "area_m2": round(gross_area, 3),
        "construction": {"identifier": f"wall-construction-{wall_u:.3f}", "u_value_wm2k": wall_u},
        "apertures": [],
    }


def build_honeybee_model(mercure_input: MercureInput) -> "tuple[Dict, BuildDiagnostics]":
    """Returns (model_dict, diagnostics). Raises HoneybeeTranslationError on
    missing/invalid required data — never silently substitutes a default
    for a physically-required value (GC-COOLING-05A pt.3)."""
    diagnostics = BuildDiagnostics()
    geometry = mercure_input.geometry
    envelope = mercure_input.envelope

    if geometry.length_m <= 0 or geometry.width_m <= 0 or geometry.height_m <= 0:
        raise HoneybeeTranslationError(
            f"Geometry must have positive dimensions, got "
            f"{geometry.length_m}x{geometry.width_m}x{geometry.height_m} m."
        )
    if envelope.walls.u_value_wm2k <= 0 or envelope.roof.u_value_wm2k <= 0 or envelope.floor.u_value_wm2k <= 0:
        raise HoneybeeTranslationError("Envelope U-values must be positive.")

    walls_by_facade = {}
    for facade in ("north", "south", "east", "west"):
        walls_by_facade[facade] = _wall_face(
            facade, geometry.length_m, geometry.width_m, geometry.height_m, envelope.walls.u_value_wm2k
        )

    for glazing_facade in mercure_input.glazing.facades:
        wall = walls_by_facade.get(glazing_facade.facade)
        if wall is None:
            diagnostics.warnings.append(
                f"Glazing facade '{glazing_facade.facade}' has no matching wall face; skipped."
            )
            continue
        if glazing_facade.area_m2 > wall["area_m2"]:
            raise HoneybeeTranslationError(
                f"Glazing area {glazing_facade.area_m2} m2 on facade '{glazing_facade.facade}' exceeds "
                f"that wall's gross area {wall['area_m2']} m2."
            )
        wall["apertures"].append(
            {
                "type": "Aperture",
                "identifier": f"aperture-{glazing_facade.facade}",
                "area_m2": round(glazing_facade.area_m2, 3),
                "construction": {
                    "identifier": f"glazing-construction-{glazing_facade.u_value_wm2k:.3f}",
                    "u_value_wm2k": glazing_facade.u_value_wm2k,
                    "solar_heat_gain_coefficient": glazing_facade.solar_factor,
                },
                # protection_factor/shade_factor fold MERCURE's shading
                # model into a single static transmittance multiplier
                # instead of a real Honeybee WindowConstructionShade —
                # dynamic/scheduled shading is not translated (assumption
                # logged below).
                "static_shading_transmittance": round(glazing_facade.protection_factor * glazing_facade.shade_factor, 4),
            }
        )
    diagnostics.assumptions.append(
        "Solar protections (blinds/brise-soleil/overhang/...) are folded into a single static "
        "aperture transmittance multiplier, not a scheduled or geometric Honeybee shade."
    )

    roof_face = {
        "type": "Face",
        "identifier": "roof",
        "face_type": "RoofCeiling",
        "boundary_condition": "Outdoors",
        "area_m2": round(geometry.floor_area_m2, 3),
        "construction": {"identifier": f"roof-construction-{envelope.roof.u_value_wm2k:.3f}", "u_value_wm2k": envelope.roof.u_value_wm2k},
        "apertures": [],
    }
    floor_face = {
        "type": "Face",
        "identifier": "floor",
        "face_type": "Floor",
        "boundary_condition": envelope.floor_boundary,
        "area_m2": round(geometry.floor_area_m2, 3),
        "construction": {"identifier": f"floor-construction-{envelope.floor.u_value_wm2k:.3f}", "u_value_wm2k": envelope.floor.u_value_wm2k},
        "apertures": [],
    }
    diagnostics.assumptions.append(
        "Each construction is exported as a single equivalent-U-value layer, not a real layered "
        "material assembly (Honeybee OpaqueConstruction would need individual material thicknesses/"
        "conductivities, which MERCURE's snapshot does not carry)."
    )

    equipment_power_density_wm2 = 0.0
    if geometry.floor_area_m2 > 0:
        equipment_power_density_wm2 = sum(
            e.quantity * e.unit_power_w * e.load_factor * e.simultaneity_factor * e.operating_fraction
            for e in mercure_input.equipment
        ) / geometry.floor_area_m2
    diagnostics.assumptions.append(
        "All internal equipment loads are aggregated into a single ElectricEquipment power density for "
        "the room, not modeled as individual Honeybee equipment objects with their own schedules."
    )

    room = {
        "type": "Room",
        "identifier": "room-greencube",
        "display_name": "GreenCube",
        "geometry": {
            "length_m": geometry.length_m,
            "width_m": geometry.width_m,
            "height_m": geometry.height_m,
            "floor_area_m2": geometry.floor_area_m2,
            "volume_m3": geometry.volume_m3,
        },
        "faces": [walls_by_facade[f] for f in ("north", "south", "east", "west")] + [roof_face, floor_face],
        "properties": {
            "energy": {
                "people": {
                    "people_per_area": (
                        mercure_input.occupancy.usual_occupants / geometry.floor_area_m2
                        if geometry.floor_area_m2 > 0
                        else 0.0
                    ),
                    "occupancy_schedule_fraction": mercure_input.occupancy.occupancy_fraction,
                    "sensible_gain_per_person_w": mercure_input.occupancy.sensible_gain_per_person_w,
                    "latent_gain_per_person_g_h": mercure_input.occupancy.latent_gain_per_person_g_h,
                },
                "lighting": {
                    "watts_per_area": mercure_input.lighting.power_density_wm2,
                    "schedule_fraction": mercure_input.lighting.usage_fraction,
                },
                "electric_equipment": {"watts_per_area": round(equipment_power_density_wm2, 3)},
                "infiltration": {
                    "air_changes_per_hour": mercure_input.infiltration.air_changes_per_hour,
                    "method": mercure_input.infiltration.method,
                },
                "ventilation": {
                    "system_type": mercure_input.ventilation.system_type,
                    "airflow_m3h": mercure_input.ventilation.airflow_m3h,
                    "heat_recovery_efficiency": mercure_input.ventilation.heat_recovery_efficiency,
                },
                "setpoints": {
                    "cooling_day_c": mercure_input.comfort.cooling_setpoint_day_c,
                    "cooling_night_c": mercure_input.comfort.cooling_setpoint_night_c,
                },
            }
        },
    }

    model = {
        "type": "Model",
        "identifier": f"gc-study-{mercure_input.study_id}-snapshot-{mercure_input.snapshot_id}",
        "units": "Meters",
        "north_angle_deg": 0,
        "rooms": [room],
        "source_snapshot_hash": mercure_input.snapshot_hash,
    }
    diagnostics.assumptions.append(
        "north_angle_deg is always 0: facade compass orientation is already resolved into each "
        "face's azimuth_label upstream (GC-COOLING-09's rotation), so no additional model-level "
        "rotation is applied here."
    )

    canonical = json.dumps(model, sort_keys=True, separators=(",", ":"))
    diagnostics.checksum_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return model, diagnostics
