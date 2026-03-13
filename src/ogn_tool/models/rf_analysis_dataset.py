from dataclasses import dataclass, field
from typing import Any, Optional

from .rf_analysis_results import RFAnalysisResults
from .rf_observation_vector import RFObservationVector


@dataclass
class RFAnalysisDataset:

    observations: Any

    diagnostics: Optional[object] = None
    results: RFAnalysisResults = field(default_factory=RFAnalysisResults)


    @property
    def feature_matrix(self):
        """Backward-compatible alias to results.feature_matrix."""
        return self.results.feature_matrix

    @feature_matrix.setter
    def feature_matrix(self, value):
        self.results.feature_matrix = value

    def available_fields(self) -> set[str]:
        """Return currently available dataset fields for stage dependency checks."""

        fields: set[str] = set()
        if self.observations is not None:
            fields.add("observations")
        if self.results.feature_matrix is not None:
            fields.add("feature_matrix")
        if self.results.coverage is not None:
            fields.add("coverage")
        if self.results.visibility is not None:
            fields.add("visibility")
        if self.results.blind_zones is not None:
            fields.add("blind_zones")
        if self.results.antenna_pattern is not None:
            fields.add("antenna_pattern")
        if self.results.antenna_shadow_sectors is not None:
            fields.add("antenna_shadow_sectors")
        if isinstance(self.results.metrics, dict):
            fields.add("metrics")
        return fields

    def validate(self) -> None:
        """Validate structural integrity of dataset after pipeline execution."""

        if self.observations is None:
            raise RuntimeError("RFAnalysisDataset invalid: observations is None")

        # feature_matrix is a required intermediate pipeline artifact, not a stable public result.
        if self.results.feature_matrix is None:
            raise RuntimeError("RFAnalysisDataset invalid: results.feature_matrix is missing")

        if self.results.coverage is None:
            raise RuntimeError("RFAnalysisDataset invalid: results.coverage is missing")

        if self.results.visibility is not None and self.results.coverage is None:
            raise RuntimeError("RFAnalysisDataset invalid: results.visibility exists without results.coverage")

        if self.results.blind_zones is not None and self.results.coverage is None:
            raise RuntimeError("RFAnalysisDataset invalid: results.blind_zones exists without results.coverage")

        if self.results.antenna_pattern is not None:
            if not isinstance(self.results.antenna_pattern, dict):
                raise RuntimeError("RFAnalysisDataset invalid: results.antenna_pattern must be a dict")

            az = self.results.antenna_pattern.get("azimuth")
            p = self.results.antenna_pattern.get("probability")
            exp = self.results.antenna_pattern.get("exposure")
            rec = self.results.antenna_pattern.get("received")
            if az is None or p is None:
                raise RuntimeError("RFAnalysisDataset invalid: results.antenna_pattern missing azimuth/probability")

            bins = len(az)
            if len(p) != bins:
                raise RuntimeError("RFAnalysisDataset invalid: results.antenna_pattern azimuth/probability size mismatch")
            if exp is not None and len(exp) != bins:
                raise RuntimeError("RFAnalysisDataset invalid: results.antenna_pattern exposure size mismatch")
            if rec is not None and len(rec) != bins:
                raise RuntimeError("RFAnalysisDataset invalid: results.antenna_pattern received size mismatch")

            bearing = getattr(self.results.feature_matrix, "bearing", None)
            if bearing is not None and exp is not None:
                total_exposure = float(sum(exp))
                if total_exposure > float(len(bearing)):
                    raise RuntimeError(
                        "RFAnalysisDataset invalid: results.antenna_pattern exposure exceeds feature_matrix size"
                    )

        self.results.validate()

