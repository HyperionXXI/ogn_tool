from dataclasses import dataclass
from typing import List, Optional

from .rf_observation_vector import RFObservationVector


@dataclass
class RFAnalysisDataset:

    observations: List[RFObservationVector]

    coverage: Optional[object] = None
    visibility: Optional[object] = None
    blind_zones: Optional[object] = None
    diagnostics: Optional[object] = None
    feature_matrix: Optional[dict] = None
