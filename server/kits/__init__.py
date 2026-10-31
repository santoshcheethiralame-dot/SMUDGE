"""Every case kit in this package registers itself: drop a module with a Kit subclass in here and it is live.
Cases are ordered by their `num`."""
import importlib
import inspect
import pkgutil

from .base import Kit


def _discover() -> dict[str, Kit]:
    found = []
    for m in pkgutil.iter_modules(__path__):
        if m.name == "base":
            continue
        mod = importlib.import_module(f".{m.name}", __name__)
        found += [cls() for _, cls in inspect.getmembers(mod, inspect.isclass)
                  if issubclass(cls, Kit) and cls is not Kit and cls.__module__ == mod.__name__]
    return {k.id: k for k in sorted(found, key=lambda k: k.num) if k.id}


REGISTRY: dict[str, Kit] = _discover()


def add_generated(spec: dict) -> Kit:
    """Register a case written as data (kits/generated/*.json, or fresh from the Author agents)."""
    from .generic import GenericKit
    kit = REGISTRY[spec["id"]] = GenericKit(spec, REGISTRY[spec["borrow"]])
    return kit


def _load_generated():
    from .generic import load_specs
    for spec in load_specs():
        try:
            add_generated(spec)
        except Exception as e:      # one bad spec must not take the server down
            print(f"skipped generated case {spec.get('id')}: {e}")


_load_generated()
DEFAULT = "density"


def get(kit_id: str | None) -> Kit:
    return REGISTRY[kit_id or DEFAULT]
