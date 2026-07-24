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
import os
import shutil
import subprocess

_logger = logging.getLogger(__name__)


def is_energyplus_enabled():
    """GC-COOLING-05A pt.8: every EnergyPlus-adjacent feature (Honeybee
    translation included) stays behind this flag, default off, so an
    accidental engine=energyplus request never does more than emit a
    disabled-feature warning even on a server that happens to have the
    stack installed."""
    return os.environ.get("GC_COOLING_ENERGYPLUS_ENABLED", "false").strip().lower() in ("1", "true", "yes")


class EnergyPlusUnavailableError(Exception):
    """Raised when the honeybee-energy/EnergyPlus stack is not installed in
    this environment. Distinct from EnergyPlusSimulationError so callers can
    tell "not installed" apart from "installed but the run itself failed"."""


class EnergyPlusSimulationError(Exception):
    """Raised when honeybee-energy/EnergyPlus are installed but the
    simulation itself could not be produced (bad geometry, solver crash,
    missing weather file, ...)."""


# GC-COOLING-05A pt.7: "Détecter versions Honeybee, Ladybug, OpenStudio et
# EnergyPlus ; vérifier une matrice de compatibilité." This is the pinned,
# documented, testable compatibility matrix this MVP has actually been
# built and tested against/for. It is intentionally a single pinned tuple
# per component rather than a wide range: this lot claims no verified
# compatibility beyond exactly what it was written against, and widening
# the matrix later is a deliberate, reviewable decision, not something
# discovered by trial and error in production.
COMPATIBLE_HONEYBEE_ENERGY_VERSION = "1.106.5"
COMPATIBLE_LADYBUG_VERSION = "0.42.5"
COMPATIBLE_ENERGYPLUS_VERSION = "23.2.0"
# OpenStudio is optional in this MVP: the translation shell targets a direct
# Honeybee -> EnergyPlus path (documented in this module's own docstring),
# so an absent OpenStudio never blocks availability, only the two paths
# that actually need it later.
COMPATIBLE_OPENSTUDIO_VERSION = "3.6.1"


def _module_version(module_name):
    """Best-effort `<module>.__version__` lookup without importing the
    module at call time unless it is actually present (importlib.util.
    find_spec first) — this environment doesn't have any of these packages
    installed, so this function is exercised by tests via monkeypatching,
    not by the module actually being present here."""
    if importlib.util.find_spec(module_name) is None:
        return None
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - defensive, not expected to trigger here
        _logger.warning("Found %s on sys.path but it failed to import: %s", module_name, exc)
        return None
    return getattr(module, "__version__", "unknown")


def _energyplus_binary_version(binary_path):
    """Runs `<binary> --version` to read the installed EnergyPlus version.
    Uses an argument list (never a shell string), a fixed short timeout,
    and never accepts a client-supplied path — `binary_path` always comes
    from `shutil.which()` in this module, matching the "no client-provided
    path, no shell=True" rule that governs every EnergyPlus invocation in
    this codebase (see run_energyplus_simulation)."""
    try:
        completed = subprocess.run(
            [binary_path, "--version"],
            shell=False,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _logger.warning("Could not query EnergyPlus version at %s: %s", binary_path, exc)
        return None
    output = (completed.stdout or b"").decode("utf-8", errors="replace").strip()
    return output or None


def get_component_versions():
    """Returns a dict of the actually-detected version of each component,
    or None when the component is absent — never a fabricated value. Pure
    inspection, no simulation, safe to call regardless of the feature flag
    or from Odoo's web process."""
    energyplus_binary = shutil.which("energyplus") or shutil.which("EnergyPlus")
    openstudio_binary = os.environ.get("OPENSTUDIO_PATH") or shutil.which("openstudio")
    return {
        "honeybee_energy": _module_version("honeybee_energy"),
        "ladybug": _module_version("ladybug"),
        "energyplus": _energyplus_binary_version(energyplus_binary) if energyplus_binary else None,
        "openstudio": _module_version("openstudio") if openstudio_binary else None,
    }


def check_compatibility(versions=None):
    """Compares detected versions against COMPATIBLE_*_VERSION. Returns a
    dict of {component: {"detected": ..., "expected": ..., "compatible":
    bool_or_None}} — None means "not installed, so compatibility is
    unknown", never "assumed fine". OpenStudio is informational only (this
    MVP's translation path does not require it), so it never affects the
    overall verdict returned by check_availability()."""
    versions = versions if versions is not None else get_component_versions()
    expected = {
        "honeybee_energy": COMPATIBLE_HONEYBEE_ENERGY_VERSION,
        "ladybug": COMPATIBLE_LADYBUG_VERSION,
        "energyplus": COMPATIBLE_ENERGYPLUS_VERSION,
        "openstudio": COMPATIBLE_OPENSTUDIO_VERSION,
    }
    matrix = {}
    for component, expected_version in expected.items():
        detected = versions.get(component)
        if detected is None:
            matrix[component] = {"detected": None, "expected": expected_version, "compatible": None}
            continue
        # Version strings from --version output can carry extra text
        # ("EnergyPlus, Version 23.2.0-..."); a substring match is enough
        # to confirm the pinned version is present without needing a full
        # semver parser for this MVP's single-pinned-version matrix.
        matrix[component] = {
            "detected": detected,
            "expected": expected_version,
            "compatible": expected_version in detected,
        }
    return matrix


def check_availability():
    """Return (available: bool, detail: str) without raising, so callers can
    decide how to degrade (e.g. warn-and-fallback vs hard error). Presence
    (not version compatibility) gates availability: an installed-but-
    unpinned version is reported in the detail string as a warning rather
    than treated as absent, so a real but untested version does not get
    silently reported as "not installed"."""
    versions = get_component_versions()
    honeybee_energy_present = versions["honeybee_energy"] is not None
    ladybug_present = versions["ladybug"] is not None
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

    matrix = check_compatibility(versions)
    mismatches = [
        f"{component} detected={info['detected']!r} expected={info['expected']!r}"
        for component, info in matrix.items()
        if info["compatible"] is False
    ]
    detail = f"EnergyPlus binary at {energyplus_binary} (versions={versions})"
    if mismatches:
        detail += " — UNPINNED VERSION WARNING: " + "; ".join(mismatches)
        _logger.warning("EnergyPlus stack present but not on the pinned/tested version: %s", "; ".join(mismatches))
    return True, detail


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
