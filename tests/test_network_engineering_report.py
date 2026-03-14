from __future__ import annotations

from ogn_tool.reporting.report_builder import build_network_engineering_report


class DummyResults:
    def __init__(self, metrics):
        self.network_metrics = metrics



def test_station_corridor_interpretation() -> None:
    results = DummyResults(
        {
            "station_angular_entropy": {"A": 0.1},
            "shadow_risk_scores": {"A": 0.9},
        }
    )

    report = build_network_engineering_report(results)

    assert "corridor" in report.station_diagnostics["A"].interpretation.lower()



def test_builder_accepts_dict_input() -> None:
    results = {
        "network_metrics": {
            "station_angular_entropy": {"A": 0.8},
            "shadow_risk_scores": {"A": 0.2},
        }
    }

    report = build_network_engineering_report(results)

    assert "robust" in report.station_diagnostics["A"].interpretation.lower()


def test_reporting_package_exports_canonical_report_model() -> None:
    from ogn_tool.reporting import NetworkEngineeringReport as package_model
    from ogn_tool.reporting.models import NetworkEngineeringReport as legacy_models_model
    from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport as canonical_model
    from ogn_tool.reporting.report_models import NetworkEngineeringReport as legacy_report_model

    assert package_model is canonical_model
    assert legacy_models_model is canonical_model
    assert legacy_report_model is canonical_model


def test_builder_surfaces_missing_metric_inputs() -> None:
    results = {"network_metrics": {}}

    report = build_network_engineering_report(results)

    assert "network_summary missing from network_metrics" in report.input_warnings
    assert "station_angular_entropy missing from network_metrics" in report.input_warnings
    assert "shadow_risk_scores missing from network_metrics" in report.input_warnings


def test_builder_surfaces_invalid_metric_types() -> None:
    results = {
        "network_metrics": {
            "network_summary": 1.0,
            "station_angular_entropy": 3.14,
            "shadow_risk_scores": [],
        }
    }

    report = build_network_engineering_report(results)

    assert "network_summary expected dict but got float" in report.input_warnings
    assert "station_angular_entropy expected dict but got float" in report.input_warnings
    assert "shadow_risk_scores expected dict but got list" in report.input_warnings


def test_builder_surfaces_pipeline_contract_warnings() -> None:
    results = {
        "network_metrics": {
            "_contract_warnings": [
                "network_redundancy not produced by analysis pipeline",
            ]
        }
    }

    report = build_network_engineering_report(results)

    assert "network_redundancy not produced by analysis pipeline" in report.input_warnings


def test_builder_surfaces_pipeline_coherence_warnings() -> None:
    results = {
        "network_metrics": {
            "_coherence_warnings": [
                "High network redundancy reported but strong station dependencies detected.",
            ]
        }
    }

    report = build_network_engineering_report(results)

    assert "High network redundancy reported but strong station dependencies detected." in report.input_warnings


def test_builder_surfaces_pipeline_confidence_warnings() -> None:
    results = {
        "network_metrics": {
            "_confidence_warnings": [
                "Insufficient dataset for reliable network inference.",
            ]
        }
    }

    report = build_network_engineering_report(results)

    assert "Insufficient dataset for reliable network inference." in report.input_warnings
