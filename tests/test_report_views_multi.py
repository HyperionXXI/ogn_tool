from ogn_tool.reporting.report_views import get_network_status

def test_report_views_on_sample_report(sample_network_report):
    status = get_network_status(sample_network_report)
    assert isinstance(status, dict)
