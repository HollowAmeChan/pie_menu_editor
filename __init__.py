bl_info = {
    "name": "Pie Menu Editor Fork",
    "author": "roaoao, pluglug",
    "version": (1, 19, 50),
    "blender": (3, 2, 0),
    "tracker_url": "http://blenderartists.org/forum/showthread.php?392910",
    "wiki_url": (
        "https://archive.blender.org/wiki/2015/index.php/User:Raa/Addons/Pie_Menu_Editor/"
    ),
    "doc_url": "https://pluglug.github.io/pme-docs",
    "category": "User Interface",
}

import importlib
import sys


if "core" in locals():
    core = importlib.reload(core)
else:
    from . import core


def _expose_legacy_modules():
    for module_name in core.MODULES:
        qualified_name = f"{core.__name__}.{module_name}"
        module = sys.modules.get(qualified_name)
        if module is None:
            continue
        globals()[module_name] = module
        sys.modules[f"{__name__}.{module_name}"] = module


def __getattr__(name):
    if name not in core.MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{core.__name__}.{name}")
    globals()[name] = module
    sys.modules[f"{__name__}.{name}"] = module
    return module


_expose_legacy_modules()


def register():
    core.register()


def unregister():
    core.unregister()
