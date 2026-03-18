from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from ogn_tool.domain.rf_analysis_results import RFAnalysisResults

@dataclass
class RFAnalysisReport:
    metadata: Dict[str, Any]
    summary_metrics: Dict[str, Any]
    rf_metrics: Dict[str, Any]
    coverage_metrics: Dict[str, Any]
    network_metrics: Dict[str, Any]
    diagnostics: Optional[Dict[str, Any]] = None


def build_rf_analysis_report(results: RFAnalysisResults) -> RFAnalysisReport:
    # Extract fields from results
    metadata = {
        "report_version": 1,
        # Add more metadata as needed (timestamp, git info, etc.)
    }
    summary_metrics = results.metrics or {}
    rf_metrics = getattr(results, "rf_metrics", {}) or {}
    coverage_metrics = getattr(results, "coverage", {}) or {}
    network_metrics = results.network_metrics or {}

    # Add network_graph to network_metrics
    network_graph = getattr(results, "network_graph", None)
    if network_graph is not None:
        network_metrics["network_graph"] = network_graph

    # Diagnostics always a dict
    diagnostics = getattr(results, "diagnostics", {}) or {}
    # Add spatial_observations and station_suggestions to diagnostics
    spatial_obs = getattr(results, "spatial_observations", None)
    station_suggestions = getattr(results, "station_suggestions", None)
    diagnostics["spatial_observations"] = spatial_obs
    diagnostics["station_suggestions"] = station_suggestions

    return RFAnalysisReport(
        metadata=metadata,
        summary_metrics=summary_metrics,
        rf_metrics=rf_metrics,
        coverage_metrics=coverage_metrics,
        network_metrics=network_metrics,
        diagnostics=diagnostics,
    )


def export_rf_analysis_report(report: RFAnalysisReport, output_dir: str):
    import os
    import json
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "report.json")
    metadata_path = os.path.join(output_dir, "run_metadata.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(report.metadata, f, indent=2, ensure_ascii=False)
