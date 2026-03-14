from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalysisRun:
    run_id: str
    created_at: str
    engine_version: str
    dataset_summary: dict[str, Any] = field(default_factory=dict)
    config_summary: dict[str, Any] = field(default_factory=dict)
