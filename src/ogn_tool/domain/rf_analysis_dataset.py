from dataclasses import dataclass, field
from typing import Any, Optional

from ogn_tool.analysis.observation_contract import (
    RFObservationsContract,
    classify_observations,
    inspect_observations,
)
from ogn_tool.models.rf_analysis_results import RFAnalysisResults


@dataclass
class RFAnalysisDataset:

    observations: Any

    diagnostics: Optional[object] = None
    # Optional, non-breaking quality indicator for the observations payload.
    # Populated on demand via evaluate_input_quality() and otherwise ignored
    # by the pipeline.
    input_quality: Optional[str] = None
    observations_contract: Optional[RFObservationsContract] = None
    results: RFAnalysisResults = field(default_factory=RFAnalysisResults)

    def __post_init__(self) -> None:
        """Best-effort initialization of input quality metadata.

        This is non-breaking by design: any error in inspection or
        classification is swallowed so that existing callers and
        pipeline execution remain unaffected.
        """
        try:
            self.evaluate_input_quality()
        except Exception:
            self.input_quality = None
            self.observations_contract = None


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

    def evaluate_input_quality(self) -> str:
        """Inspect and classify the observations payload.

        This helper is intentionally non-breaking:
        - It never raises.
        - It does not affect pipeline execution; it only records a
          human-readable quality flag and the inspected contract.
        """

        contract = inspect_observations(self.observations)
        classification = classify_observations(contract)
        self.observations_contract = contract
        self.input_quality = classification
        return classification

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

