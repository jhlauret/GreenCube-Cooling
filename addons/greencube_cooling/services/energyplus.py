# -*- coding: utf-8 -*-
"""Honeybee/EnergyPlus orchestration for GC-COOLING-05A/15.

This module owns the *dispatch* contract between a calculation snapshot's
`requested_engine` (quick_solver / energyplus / both) and an actual detailed
building-energy simulation. It deliberately does not fabricate a plausible
result when the simulation stack is missing: honeybee-energy and the
EnergyPlus binary are heavy, separately-installed dependencies (not
pip-installable Python-only packages — EnergyPlus itself is a ~600MB
compiled application), and this module's job is to fail loudly and
specifically when they are absent, so the caller can fall back to MERCURE
and tell the user why, rather than presenting a number nobody actually
computed.

When honeybee-energy/EnergyPlus *are* installed, `run_energyplus_simulation`
still only builds the translation shell (Honeybee Room from MercureInput
geometry/envelope/glazing, an IdealAirSystem, an EPW-driven design-day
sizing run) — matching what GC-COOLING-15 describes as the orchestration
boundary; the day-to-day quick path stays MERCURE.
"""
import importlib.util
import logging
import shutil

_logger = logging.getLogger(__name__)


class EnergyPlusUnavailableError(Exception):
    """Raised when the honeybee-energy/EnergyPlus stack is not installed in
    this environment. Distinct from EnergyPlusSimulationError so callers can
    tell "not installed" apart from "installed but the run itself failed"."""


class EnergyPlusSimulationError(Exception):
    """Raised when honeybee-energy/EnergyPlus are installed but the
    simulation itself could not be produced (bad geometry, solver crash,
    missing weather file, ...)."""


def check_availability():
    """Return (available: bool, detail: str) without raising, so callers can
    decide how to degrade (e.g. warn-and-fallback vs hard error)."""
    honeybee_energy_present = importlib.util.find_spec("honeybee_energy") is not None
    ladybug_present = importlib.util.find_spec("ladybug") is not None
    energyplus_binary = shutil.which("energyplus") or shutil.which("EnergyPlus")

    missing = []
    if not honeybee_energy_present:
        missing.append("honeybee-energy (pip package)")
    if not ladybug_present:
        missing.append("ladybug (pip package)")
    if not energyplus_binary:
        missing.append("EnergyPlus binary (separate installer, not pip-installable)")

    if missing:
        return False, "Missing: " + ", ".join(missing)
    return True, f"EnergyPlus binary at {energyplus_binary}"


def run_energyplus_simulation(mercure_input, epw_path=None):
    """Translate a MercureInput into a Honeybee model and run an EnergyPlus
    design-day cooling-load simulation.

    Raises EnergyPlusUnavailableError if the stack isn't installed. Only
    reaches the actual translation/run logic when it is — that logic isn't
    implemented yet (GC-COOLING-15 orchestration, not the simulation
    internals, was in scope for this lot), so it raises
    EnergyPlusSimulationError with a clear "not yet implemented" message
    rather than silently falling back, so the distinction between "can't run
    EnergyPlus here" and "EnergyPlus ran and failed" stays honest.
    """
    available, detail = check_availability()
    if not available:
        raise EnergyPlusUnavailableError(
            f"EnergyPlus/Honeybee simulation requested but the stack is not installed on this server ({detail}). "
            "Install honeybee-energy, ladybug, and the EnergyPlus binary, or request engine=quick_solver instead."
        )

    # Reaching here means the stack is genuinely installed. The
    # geometry/zone/schedule translation and the design-day run itself are
    # out of scope for this lot; see GC-COOLING-15 for the full mapping this
    # would implement (Room from Geometry+Envelope+Glazing, IdealAirSystem,
    # ScheduleRuleset from Occupancy/Equipment/Lighting, EPW design days from
    # the study's climate scenarios).
    raise EnergyPlusSimulationError(
        "honeybee-energy/EnergyPlus are installed, but the geometry translation and simulation run "
        "(GC-COOLING-15) are not implemented yet. Use engine=quick_solver for a real result."
    )
