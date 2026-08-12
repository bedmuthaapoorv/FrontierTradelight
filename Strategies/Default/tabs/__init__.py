"""Plugin registry for app.py's tabs.

Each module in this package is a self-contained tab: it must define
TITLE (str, shown on the tab) and render() (called with that tab active).
An optional ORDER (int, default 100) controls left-to-right position -
lower comes first. Modules starting with "_" are ignored.

app.py never lists tabs itself; it just calls discover_tabs() and loops
over the result. Adding a new tab - your own or a merged-in one from a
fork - means dropping a new tabs/whatever.py file in this directory, not
editing a shared list. That's what keeps two people's tab additions from
colliding in the same diff.
"""

import importlib
import pkgutil

DEFAULT_ORDER = 100


def discover_tabs():
    """Imports every tabs/*.py module and returns them sorted by (ORDER, TITLE)."""
    modules = []
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        if module_name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{module_name}")
        if not hasattr(module, "TITLE") or not hasattr(module, "render"):
            raise AttributeError(
                f"tabs.{module_name} must define both TITLE and render() to be a valid tab plugin."
            )
        modules.append(module)

    return sorted(modules, key=lambda m: (getattr(m, "ORDER", DEFAULT_ORDER), m.TITLE))
