import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

sys.path.insert(0, str(SRC))

# Fixture centralisée pour les tests de reporting
import pytest

@pytest.fixture
def sample_network_report():
	return {
		"stations": [],
		"packets": [],
		"rf_metrics": {
			"coverage": 0.0,
			"packet_rate": 0,
			"station_count": 0
		},
		"risk_summary": {
			"critical_station_count": 0,
			"risk_score": 0
		}
	}
