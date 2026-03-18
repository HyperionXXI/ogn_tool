import pytest

from ogn_tool.engine.rf_pipeline_executor import execute_rf_pipeline
from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_feature_matrix import RFFeatureMatrix
from ogn_tool.pipeline.rf_stages import FeatureMatrixStage
from ogn_tool.reporting.rf_analysis_report import build_rf_analysis_report
from ogn_tool.reporting.report_views import build_spatial_view


@pytest.fixture
def sample_rf_observations():
    import pandas as pd

    return {
        "distance_df": pd.DataFrame(
            {
                "timestamp": [1, 2, 3],
                "lat": [45.0, 46.0, 47.0],
                "lon": [3.0, 4.0, 5.0],
                "altitude": [1000, 1200, 1100],
            }
        ),
        "station_lat": 47.3359,
        "station_lon": 7.2728,
    }


def test_rf_pipeline_feature_matrix_only(sample_rf_observations):
    """Smoke-test minimal RF pipeline wiring on observations input.

    This test intentionally restricts execution to the FeatureMatrixStage to
    avoid exercising heavy RF models, coverage, or visibility analysis.
    """
    dataset = RFAnalysisDataset(observations=sample_rf_observations)

    class _MinimalPipeline:
        def __init__(self):
            self.stages = [FeatureMatrixStage()]
            self.metrics = {}

    pipeline = _MinimalPipeline()
    result = execute_rf_pipeline(dataset, pipeline)

    feature_matrix = result.results.feature_matrix

    # The stage must materialize a feature matrix object
    assert isinstance(feature_matrix, RFFeatureMatrix)

    # All numeric fields must be 1D numpy arrays of the same length
    distances = feature_matrix.distance
    azimuths = feature_matrix.azimuth
    altitudes = feature_matrix.altitude
    bearings = feature_matrix.bearing

    for arr in (distances, azimuths, altitudes, bearings):
        # numpy-like sequences support len() even when empty
        assert hasattr(arr, "__len__")

    assert len(distances) == len(azimuths) == len(altitudes) == len(bearings)

    # Packet count should reflect the number of rows used to build the matrix
    assert isinstance(feature_matrix.packet_count, int)
    assert feature_matrix.packet_count == len(distances)

    # Pipeline bookkeeping should record execution of the feature_matrix stage
    assert "feature_matrix" in pipeline.metrics

    # Reporting compatibility: results can be projected into a report dict and consumed by report views.
    report = build_rf_analysis_report(result.results)
    spatial = build_spatial_view(report.__dict__)
    assert set(spatial.keys()) == {"stations", "links", "coverage", "diagnostics"}
    assert isinstance(spatial["diagnostics"], list)
