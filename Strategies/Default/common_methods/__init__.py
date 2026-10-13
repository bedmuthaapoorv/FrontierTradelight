"""Common Method Library: reusable, verified building blocks for generated
strategies. One public function per module, named after the module.
Modules are immutable once added - a behaviour change gets a new name
(e.g. `find_rising_trendline_v2`) so existing strategies and backtests keep
reproducing exactly. See RULES_GUIDE.md "Common Method Library"."""

import importlib
import pkgutil

__all__ = []


def __getattr__(name):
    # Methods saved after this package was first imported (e.g. by a compile
    # inside the long-running API process) are loaded on first use.
    if name.startswith("_"):
        raise AttributeError(name)
    importlib.invalidate_caches()
    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    func = getattr(module, name)
    globals()[name] = func
    if name not in __all__:
        __all__.append(name)
    return func


# __getattr__ is defined before this loop so a method that does
# `from common_methods import other_method` while the package is still
# initialising gets the function, not the `other_method` submodule (the
# import system's fallback), which would fail later with
# "'module' object is not callable".
for _info in pkgutil.iter_modules(__path__):
    if _info.name.startswith("_"):
        continue
    _module = importlib.import_module(f"{__name__}.{_info.name}")
    globals()[_info.name] = getattr(_module, _info.name)
    if _info.name not in __all__:
        __all__.append(_info.name)

