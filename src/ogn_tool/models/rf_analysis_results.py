from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RFAnalysisResults:
    coverage: Optional[Any] = None
    visibility: Optional[Any] = None
    blind_zones: Optional[Any] = None
    antenna_pattern: Optional[Any] = None
    antenna_shadow_sectors: Optional[list] = None
    metrics: Optional[dict] = None
