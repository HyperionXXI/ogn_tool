from ogn_tool.kernel.rf_engine import RFAnalysisEngine
from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset


def test_kernel():
    dataset = RFAnalysisDataset(observations=[])
    engine = RFAnalysisEngine()
    results = engine.run(dataset)
    assert results is not None
