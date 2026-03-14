from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from subprocess import run
from typing import Any

from ogn_tool.models.analysis_run import AnalysisRun

from .dataset_summary import build_dataset_summary


@lru_cache(maxsize=1)
def resolve_engine_version() -> str:
    try:
        result = run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        sha = result.stdout.strip()
        if sha:
            return sha
    except Exception:
        pass

    try:
        return version("ogn_tool")
    except PackageNotFoundError:
        return "1.1"


def build_analysis_run(dataset, *, config_summary: dict[str, Any] | None = None) -> AnalysisRun:
    created_at = datetime.now(UTC)

    return AnalysisRun(
        run_id=created_at.strftime("run_%Y%m%d_%H%M%S"),
        created_at=created_at.isoformat(),
        engine_version=resolve_engine_version(),
        dataset_summary=build_dataset_summary(dataset),
        config_summary=dict(config_summary or {}),
    )


__all__ = ["build_analysis_run", "resolve_engine_version"]
