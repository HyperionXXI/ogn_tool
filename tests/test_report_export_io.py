from __future__ import annotations

import json
from pathlib import Path

from ogn_tool.reporting.report_export_io import export_network_report_json_file


def test_export_network_report_json_file(tmp_path: Path) -> None:
    contract = {
        'run_id': 'run-001',
        'metadata': {'station_id': 'S1'},
        'network_metrics': {
            'network_summary': {'packet_count': 3},
            'station_health': [],
            'station_dependency': [],
            'network_robustness': {},
            'station_placement': {},
        },
        'coverage_score': None,
    }
    output_path = tmp_path / 'artifacts' / 'report.json'

    result = export_network_report_json_file(contract, output_path)

    assert result == output_path
    assert result.exists()

    data = json.loads(result.read_text(encoding='utf-8'))
    assert set(data.keys()) == {'run_id', 'metadata', 'network_metrics', 'coverage_score'}
    assert set(data['network_metrics'].keys()) == {
        'network_summary',
        'station_health',
        'station_dependency',
        'network_robustness',
        'station_placement',
    }
