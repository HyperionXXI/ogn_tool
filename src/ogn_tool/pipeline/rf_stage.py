from __future__ import annotations

from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset


class RFAnalysisStage:
    """Base class for RF analysis pipeline stages."""

    name = "base"

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        raise NotImplementedError
