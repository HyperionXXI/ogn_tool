from __future__ import annotations

from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset


class RFAnalysisStage:
    """Base class for RF analysis pipeline stages."""

    name = "base"
    requires: list[str] = []
    produces: list[str] = []

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        raise NotImplementedError
