from ogn_tool.engine.rf_engine import RFAnalysisEngine
from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset


def test_kernel():
    dataset = RFAnalysisDataset(observations=[])
    engine = RFAnalysisEngine()
    results = engine.run(dataset)
    assert results is not None
