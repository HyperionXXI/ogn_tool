from __future__ import annotations



def detect_analysis_anomalies(diff: dict[str, object]) -> list[str]:
    anomalies: list[str] = []

    metric_diffs = diff.get("metric_diffs", {}) if isinstance(diff, dict) else {}
    if not isinstance(metric_diffs, dict):
        return anomalies

    # network summary
    network_summary = metric_diffs.get("network_summary", {})
    if isinstance(network_summary, dict):
        status = network_summary.get("network_status")
        if isinstance(status, dict) and status.get("changed"):
            anomalies.append("network status changed")

        ratio = network_summary.get("single_station_ratio")
        if isinstance(ratio, dict):
            delta = ratio.get("delta")
            if isinstance(delta, (int, float)) and delta > 0.1:
                anomalies.append("network fragility increased")

    # spof
    spof = metric_diffs.get("spof", {})
    if isinstance(spof, dict):
        station_count = spof.get("station_count")
        if isinstance(station_count, dict):
            delta = station_count.get("delta", 0)
            if isinstance(delta, (int, float)) and delta > 0:
                anomalies.append("new SPOF stations detected")

    # coverage gaps
    coverage_gaps = metric_diffs.get("coverage_gaps", {})
    if isinstance(coverage_gaps, dict):
        gap_count = coverage_gaps.get("gap_count")
        if isinstance(gap_count, dict):
            delta = gap_count.get("delta", 0)
            if isinstance(delta, (int, float)) and delta > 0:
                anomalies.append("new coverage gaps detected")

    return anomalies


__all__ = ["detect_analysis_anomalies"]
