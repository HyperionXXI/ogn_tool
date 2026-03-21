from __future__ import annotations

from typing import Any, Dict, Iterable

from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.kernel.rf_pipeline_executor import execute_rf_pipeline
from .rf_stages import (
    AntennaPatternStage,
    BlindZoneDetectionStage,
    FeatureMatrixStage,
    RFCoverageStage,
    RFDiagnosticsStage,
    VisibilityModelStage,
)


class RFAnalysisPipeline:
    def __init__(self, stages: Iterable[Any] | None = None):
        if stages is None:
            stages = [
                FeatureMatrixStage(),
                RFCoverageStage(),
                VisibilityModelStage(),
                BlindZoneDetectionStage(),
                AntennaPatternStage(),
                RFDiagnosticsStage(),
            ]
        self.stages = list(stages)
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.validate_pipeline()

    def validate_pipeline(self) -> None:
        # observations are pre-existing input on RFAnalysisDataset
        produced = {"observations"}

        for stage in self.stages:
            missing = [r for r in getattr(stage, "requires", []) if r not in produced]
            if missing:
                raise RuntimeError(
                    f"Stage {getattr(stage, 'name', stage.__class__.__name__)} requires {missing} "
                    "but they were not produced by previous stages"
                )
            produced.update(getattr(stage, "produces", []))

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        return execute_rf_pipeline(dataset, self)



def run_rf_analysis_pipeline(ctx: RFAnalysisDataset) -> RFAnalysisDataset:
    """Canonical RF analysis entrypoint.

    Executes the default RF pipeline stages on a pre-built RFAnalysisDataset.
    """
    pipeline = RFAnalysisPipeline()
    return pipeline.run(ctx)


def run_rf_analysis(ctx):
    return run_rf_analysis_pipeline(ctx)
