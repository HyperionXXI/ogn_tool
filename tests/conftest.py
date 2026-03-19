import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

sys.path.insert(0, str(SRC))

import pytest


@pytest.fixture
def sample_network_report():
    return {
        'run_id': 'sample-run',
        'metadata': {},
        'network_metrics': {
            'network_summary': {
                'network_status': 'unknown',
                'critical_station_count': 0,
                'warning_station_count': 0,
            },
            'station_health': [],
            'station_dependency': [],
            'network_robustness': {},
            'station_placement': {},
        },
        'coverage_score': None,
    }
