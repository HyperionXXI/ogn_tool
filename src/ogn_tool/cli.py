# src/ogn_tool/cli.py
from __future__ import annotations

import runpy
from pathlib import Path

from .cli_runs import main as _runs_main



def dashboard() -> None:
    # Runs apps/dashboard.py as a script
    runpy.run_path(str(Path(__file__).resolve().parents[2] / 'apps' / 'dashboard.py'), run_name='__main__')



def collector() -> None:
    runpy.run_path(str(Path(__file__).resolve().parents[2] / 'scripts' / 'collector.py'), run_name='__main__')



def runs() -> None:
    """Run the thin run-history CLI consumer."""
    raise SystemExit(_runs_main())
