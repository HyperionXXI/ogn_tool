from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset


def test_dataset_contract_fields():
    dataset = RFAnalysisDataset(observations=[])

    # Frozen contract checks
    assert hasattr(dataset, "feature_matrix")
    assert hasattr(dataset, "results")
    assert hasattr(dataset.results, "coverage")
    assert hasattr(dataset.results, "visibility")
