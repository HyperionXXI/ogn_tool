from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle
from ogn_tool.reporting.views.dashboard_views import build_dashboard_payload


def test_report_e2e_contract(tmp_path: Path) -> None:
    report = NetworkEngineeringReport(
        network_summary={'packet_count': 17, 'coverage_score': 0.61},
        station_health_table=pd.DataFrame([
            {'station_id': 'S1', 'health_status': 'GOOD'},
            {'station_id': 'S2', 'health_status': 'WARNING'},
        ]),
        station_dependency=pd.DataFrame([
            {'station_id': 'S1', 'depends_on_station': 'S2', 'dependency_strength': 0.4},
        ]),
        network_redundancy={'redundancy_score': 0.7},
        analysis_stats={'station_placement': {'candidate_count': 3}},
    )

    bundle_dir = export_analysis_run_bundle(
        report,
        tmp_path / 'run-e2e',
        run_metadata={'run_id': 'run-e2e'},
        dataset_identity={'station_id': 'FK50887'},
    )

    saved_report = json.loads((bundle_dir / 'report.json').read_text(encoding='utf-8'))

    assert set(saved_report.keys()) == {'run_id', 'metadata', 'network_metrics', 'coverage_score'}
    assert set(saved_report['network_metrics'].keys()) == {
        'network_summary',
        'station_health',
        'station_dependency',
        'network_robustness',
        'station_placement',
    }

    payload = build_dashboard_payload(saved_report)

    assert payload['debug']['run_id'] == 'run-e2e'
    assert payload['network_summary']['packet_count'] == 17
    assert payload['network_summary']['coverage_score'] == 0.61
    assert payload['network_summary']['station_count'] == 2
    assert isinstance(payload['stations'], list)
    assert payload['intelligence']['alerts'] == [
        {'type': 'degraded_station', 'severity': 'warning', 'station_id': 'S2'}
    ]
