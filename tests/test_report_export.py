from __future__ import annotations

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.report_export import export_network_report_json



def test_export_network_report_json_structure() -> None:
    report = NetworkEngineeringReport()

    data = export_network_report_json(report)

    assert 'report_metadata' in data
    assert 'network_status' in data
    assert 'station_health' in data
    assert 'network_risk' in data
    assert 'recommended_actions' in data



def test_export_network_report_json_metadata() -> None:
    report = NetworkEngineeringReport()

    data = export_network_report_json(report)
    meta = data['report_metadata']

    assert meta['report_version'] == '1.0'
    assert 'generated_at' in meta



def test_export_network_report_type_validation() -> None:
    try:
        export_network_report_json(None)  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == 'Expected NetworkEngineeringReport'
    else:
        raise AssertionError('Expected TypeError when report is invalid')
