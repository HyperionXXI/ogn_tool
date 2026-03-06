# src/ogn_tool/cli.py
from __future__ import annotations

import runpy
from pathlib import Path


def dashboard() -> None:
    # Runs apps/dashboard.py as a script
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "apps" / "dashboard.py"), run_name="__main__")


def collector() -> None:
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts" / "collector.py"), run_name="__main__")
