from __future__ import annotations

from pathlib import Path

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.report_export_io import export_network_report_json_file



def test_export_network_report_json_file(tmp_path: Path) -> None:
    report = NetworkEngineeringReport()
    output_path = tmp_path / 'artifacts' / 'report.json'

    result = export_network_report_json_file(report, output_path)

    assert result == output_path
    assert result.exists()

    data = result.read_text(encoding='utf-8')
    assert 'report_metadata' in data
    assert 'network_status' in data
    assert 'station_health' in data
    assert 'network_risk' in data
    assert 'recommended_actions' in data
