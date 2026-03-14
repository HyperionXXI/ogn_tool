from __future__ import annotations

import pandas as pd

from ogn_tool.reporting.report_builder import build_network_engineering_report


class DummyResults:
    def __init__(self, metrics, spatial_observations=None):
        self.network_metrics = metrics
        self.spatial_observations = spatial_observations



def test_reporting_package_exports_canonical_report_model() -> None:
    from ogn_tool.reporting import NetworkEngineeringReport as package_model
    from ogn_tool.reporting.models import NetworkEngineeringReport as legacy_models_model
    from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport as canonical_model
    from ogn_tool.reporting.report_models import NetworkEngineeringReport as legacy_report_model

    assert package_model is canonical_model
    assert legacy_models_model is canonical_model
    assert legacy_report_model is canonical_model



def test_report_builder_accepts_legacy_results_object() -> None:
    results = DummyResults(
        {
            'station_health': pd.DataFrame([{'station_id': 'S1', 'health_status': 'GOOD'}]),
            'network_summary': {'network_status': 'GOOD'},
            'station_dependency': pd.DataFrame([{'station_id': 'S1', 'depends_on_station': 'S2', 'dependency_strength': 0.2}]),
            'network_redundancy': {'redundancy_score': 0.8},
            'network_confidence': {'confidence_score': 0.9},
            'station_dominance': pd.DataFrame([{'station_id': 'S1', 'dominance_ratio': 0.1}]),
        },
        spatial_observations=pd.DataFrame([{'station_id': 'S1', 'lat': 47.0, 'lon': 7.0}]),
    )

    report = build_network_engineering_report(results)

    assert report.network_summary['network_status'] == 'GOOD'
    assert not report.station_health_table.empty
    assert not report.spatial_observations.empty



def test_report_builder_surfaces_missing_inputs() -> None:
    results = {'network_metrics': {}}

    report = build_network_engineering_report(results)

    assert 'network_summary missing from network_metrics' in report.input_warnings
    assert 'station_health missing from network_metrics' in report.input_warnings
    assert 'station_dependency missing from network_metrics' in report.input_warnings
    assert 'station_dominance missing from network_metrics' in report.input_warnings
    assert 'network_redundancy missing from network_metrics' in report.input_warnings
    assert 'network_confidence missing from network_metrics' in report.input_warnings
    assert 'spatial_observations missing from reporting inputs' in report.input_warnings



def test_report_builder_surfaces_invalid_metric_types() -> None:
    results = {
        'network_metrics': {
            'network_summary': 1.0,
            'station_health': 2.0,
            'station_dependency': {},
            'network_redundancy': [],
            'network_confidence': 3.14,
            'station_dominance': 'bad',
        },
        'spatial_observations': [],
    }

    report = build_network_engineering_report(results)

    assert 'network_summary expected dict but got float' in report.input_warnings
    assert 'station_health expected DataFrame but got float' in report.input_warnings
    assert 'station_dependency expected DataFrame but got dict' in report.input_warnings
    assert 'network_redundancy expected dict but got list' in report.input_warnings
    assert 'network_confidence expected dict but got float' in report.input_warnings
    assert 'station_dominance expected DataFrame but got str' in report.input_warnings
    assert 'spatial_observations missing from reporting inputs' in report.input_warnings



def test_report_builder_surfaces_pipeline_warnings() -> None:
    results = {
        'network_metrics': {
            '_contract_warnings': ['network_redundancy not produced by analysis pipeline'],
            '_coherence_warnings': ['High network redundancy reported but strong station dependencies detected.'],
            '_confidence_warnings': ['Insufficient dataset for reliable network inference.'],
        }
    }

    report = build_network_engineering_report(results)

    assert 'network_redundancy not produced by analysis pipeline' in report.input_warnings
    assert 'High network redundancy reported but strong station dependencies detected.' in report.input_warnings
    assert 'Insufficient dataset for reliable network inference.' in report.input_warnings
