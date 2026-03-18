import json
from ogn_tool.reporting import report_views

report = json.load(open('analysis_runs/fk50887_2026_03_11_091356_72h_offset128h/report.json'))

print('get_network_status:', report_views.get_network_status(report))
print('get_station_availability:', report_views.get_station_availability(report))
print('get_analysis_confidence:', report_views.get_analysis_confidence(report))
print('get_station_health_summary:', report_views.get_station_health_summary(report))
print('get_network_risk_summary:', report_views.get_network_risk_summary(report))
print('get_rf_signature:', report_views.get_rf_signature(report))
print('get_recommended_actions:', report_views.get_recommended_actions(report))
