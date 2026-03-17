"""
Validation sémantique des artefacts report.json pour ogn_tool.
"""

def validate_report(report):
    warnings = []
    # Vérification du volume de paquets
    packet_count = (
        report.get("rf_signature", {}).get("packet_count")
        or report.get("rf_metrics", {}).get("packet_count")
        or 0
    )
    if packet_count < 100:
        warnings.append("Low packet volume: %d" % packet_count)
    # Vérification du nombre de stations
    station_count = (
        report.get("network_metrics", {}).get("station_count")
        or report.get("network_metrics", {}).get("critical_station_count")
        or 0
    )
    if station_count < 2:
        warnings.append("Single station or missing station count: %d" % station_count)
    # Vérification de la couverture temporelle
    temporal = report.get("summary_metrics", {}).get("temporal_observability", {})
    coverage = temporal.get("temporal_coverage_ratio", 0)
    if coverage < 0.2:
        warnings.append(f"Low temporal coverage: {coverage}")
    return warnings
