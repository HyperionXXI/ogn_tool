import json
from ogn_tool.reporting.report_views import get_network_status

def test_report_views_on_multiple_artifacts():
    reports = [
        "tests/data/report_empty.json",
        "tests/data/report_small.json",
        "tests/data/report_large.json"
    ]
    for path in reports:
        with open(path) as f:
            report = json.load(f)
        status = get_network_status(report)
        assert isinstance(status, dict)
