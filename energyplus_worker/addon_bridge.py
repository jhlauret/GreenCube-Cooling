# -*- coding: utf-8 -*-
"""
Loads the pure-Python pieces of the greencube_cooling Odoo addon that this
worker needs (services/energyplus.py, services/mercure/{schemas,fixtures,
serialization}.py) WITHOUT importing the addon package itself.

Why not just `import addons.greencube_cooling.services.energyplus`? Because
that addon's own `__init__.py` does `from . import models` /
`from . import controllers`, which import `odoo` — and this worker's whole
point (GC-COOLING-15) is to run as a separate process with no Odoo runtime
and no database access at all. So instead we register lightweight
namespace-package stand-ins in sys.modules and load each file directly by
path, in dependency order, letting their existing relative imports
(`from . import schemas`) resolve against those stand-ins.

This is verified by energyplus_worker/test_worker.py, which actually loads
these modules and round-trips a fixture through them — real proof this
bridge works, not just a claim.
"""
import sys
import types
from pathlib import Path

ADDON_ROOT = Path(__file__).resolve().parent.parent / "addons" / "greencube_cooling"


def _register_namespace_package(dotted_name, path):
    existing = sys.modules.get(dotted_name)
    if existing is not None:
        return existing
    module = types.ModuleType(dotted_name)
    module.__path__ = [str(path)]
    sys.modules[dotted_name] = module
    return module


def _load_submodule(dotted_name, file_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(dotted_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = module
    spec.loader.exec_module(module)
    return module


def load():
    """Returns a namespace object with `.energyplus`, `.schemas`,
    `.serialization`, `.fixtures` attributes — the same modules the Odoo
    addon itself uses, loaded fresh each call is unnecessary since Python
    caches them in sys.modules after the first call."""
    if "greencube_cooling.services.mercure" in sys.modules:
        return types.SimpleNamespace(
            energyplus=sys.modules["greencube_cooling.services.energyplus"],
            schemas=sys.modules["greencube_cooling.services.mercure.schemas"],
            serialization=sys.modules["greencube_cooling.services.mercure.serialization"],
            fixtures=sys.modules["greencube_cooling.services.mercure.fixtures"],
        )

    if not ADDON_ROOT.is_dir():
        raise RuntimeError(f"Expected the Odoo addon at {ADDON_ROOT}, but it does not exist.")

    _register_namespace_package("greencube_cooling", ADDON_ROOT)
    _register_namespace_package("greencube_cooling.services", ADDON_ROOT / "services")
    _register_namespace_package("greencube_cooling.services.mercure", ADDON_ROOT / "services" / "mercure")

    schemas = _load_submodule(
        "greencube_cooling.services.mercure.schemas", ADDON_ROOT / "services" / "mercure" / "schemas.py"
    )
    serialization = _load_submodule(
        "greencube_cooling.services.mercure.serialization",
        ADDON_ROOT / "services" / "mercure" / "serialization.py",
    )
    fixtures = _load_submodule(
        "greencube_cooling.services.mercure.fixtures", ADDON_ROOT / "services" / "mercure" / "fixtures.py"
    )
    energyplus = _load_submodule("greencube_cooling.services.energyplus", ADDON_ROOT / "services" / "energyplus.py")

    return types.SimpleNamespace(energyplus=energyplus, schemas=schemas, serialization=serialization, fixtures=fixtures)
