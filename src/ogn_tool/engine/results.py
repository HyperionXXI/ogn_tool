from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd


@dataclass
class RFAnalysisResult:
    packets: pd.DataFrame
    distance_df: pd.DataFrame
    azimuth_df: pd.DataFrame
    coverage_grid: pd.DataFrame
    terrain_mask: pd.DataFrame | None
    metrics: Dict[str, Any]
