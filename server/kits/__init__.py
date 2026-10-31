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
    return {k.id: k for k in sorted(found, key=lambda k: k.num)}


REGISTRY: dict[str, Kit] = _discover()
DEFAULT = "density"


def get(kit_id: str | None) -> Kit:
    return REGISTRY[kit_id or DEFAULT]
