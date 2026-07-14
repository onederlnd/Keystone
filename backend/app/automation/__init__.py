# app/automation/__init__.py

import importlib
import pkgutil
from pathlib import Path

_package_dir = Path(__file__).parent

for _, module_name, _ in pkgutil.iter_modules([str(_package_dir)]):
    if module_name.endswith("_hooks"):
        importlib.import_module(f"backend.app.automation.{module_name}")
