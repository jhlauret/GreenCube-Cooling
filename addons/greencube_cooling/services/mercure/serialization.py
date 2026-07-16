# -*- coding: utf-8 -*-
"""Round-trip (de)serialization of MercureInput to/from plain dicts.

Used by GC-COOLING-13's calculation snapshot: the snapshot freezes a
MercureInput as JSON at snapshot-creation time, and action_calculate() later
rebuilds the exact same MercureInput from that frozen JSON rather than from
the (possibly since-changed) live study data.
"""
import dataclasses

from . import schemas as ms


def mercure_input_to_dict(data: ms.MercureInput) -> dict:
    return dataclasses.asdict(data)


def mercure_input_from_dict(data: dict) -> ms.MercureInput:
    envelope = data["envelope"]
    glazing = data["glazing"]
    return ms.MercureInput(
        snapshot_id=data["snapshot_id"],
        snapshot_hash=data["snapshot_hash"],
        study_id=data["study_id"],
        study_version=data["study_version"],
        climate_scenarios=[ms.ClimateScenario(**c) for c in data["climate_scenarios"]],
        geometry=ms.Geometry(**data["geometry"]),
        envelope=ms.Envelope(
            walls=ms.EnvelopeSurface(**envelope["walls"]),
            roof=ms.EnvelopeSurface(**envelope["roof"]),
            floor=ms.EnvelopeSurface(**envelope["floor"]),
            floor_boundary=envelope["floor_boundary"],
            doors=ms.EnvelopeSurface(**envelope["doors"]),
            thermal_bridge_mode=envelope["thermal_bridge_mode"],
            thermal_bridge_correction_rate=envelope["thermal_bridge_correction_rate"],
        ),
        glazing=ms.Glazing(facades=[ms.GlazingFacade(**f) for f in glazing["facades"]]),
        occupancy=ms.Occupancy(**data["occupancy"]),
        equipment=[ms.EquipmentLoad(**e) for e in data["equipment"]],
        lighting=ms.Lighting(**data["lighting"]),
        ventilation=ms.Ventilation(**data["ventilation"]),
        infiltration=ms.Infiltration(**data["infiltration"]),
        comfort=ms.Comfort(**data["comfort"]),
        margin_fraction=data["margin_fraction"],
    )
