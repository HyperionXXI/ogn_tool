from __future__ import annotations

from typing import Any


SCALAR_SUMMARY_FIELDS = {
    "aircraft_count",
    "station_count",
    "mean_stations_per_aircraft",
    "single_station_aircraft_count",
    "single_station_ratio",
    "max_overlap",
    "mean_overlap",
    "critical_station_count",
    "warning_station_count",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _delta_entry(baseline: Any, current: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "baseline": baseline,
        "current": current,
    }
    if _is_number(baseline) and _is_number(current):
        entry["delta"] = current - baseline
    return entry


def _list_or_empty(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def diff_network_summary(baseline: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, Any]:
    base = baseline or {}
    cur = current or {}

    diff: dict[str, Any] = {}
    for field in sorted(SCALAR_SUMMARY_FIELDS):
        if field in base or field in cur:
            diff[field] = _delta_entry(base.get(field), cur.get(field))

    base_status = base.get("network_status")
    cur_status = cur.get("network_status")
    if base_status is not None or cur_status is not None:
        diff["network_status"] = {
            "baseline": base_status,
            "current": cur_status,
            "changed": base_status != cur_status,
        }

    return diff


def diff_spof(baseline: Any, current: Any) -> dict[str, Any]:
    base = _list_or_empty(baseline)
    cur = _list_or_empty(current)

    base_ids = {str(row.get("station_id")) for row in base if row.get("station_id") is not None}
    cur_ids = {str(row.get("station_id")) for row in cur if row.get("station_id") is not None}

    return {
        "station_count": _delta_entry(len(base), len(cur)),
        "stations_added": sorted(cur_ids - base_ids),
        "stations_removed": sorted(base_ids - cur_ids),
    }


def diff_coverage_gaps(baseline: Any, current: Any) -> dict[str, Any]:
    base = _list_or_empty(baseline)
    cur = _list_or_empty(current)

    def _gap_key(row: dict[str, Any]) -> tuple[Any, Any]:
        return (row.get("lat"), row.get("lon"))

    base_keys = {_gap_key(row) for row in base}
    cur_keys = {_gap_key(row) for row in cur}

    return {
        "gap_count": _delta_entry(len(base), len(cur)),
        "gaps_added": sorted(cur_keys - base_keys),
        "gaps_removed": sorted(base_keys - cur_keys),
    }


def diff_snapshots(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    baseline_run = (baseline.get("analysis_run") or {}) if isinstance(baseline, dict) else {}
    current_run = (current.get("analysis_run") or {}) if isinstance(current, dict) else {}

    baseline_metrics = (baseline.get("network_metrics") or {}) if isinstance(baseline, dict) else {}
    current_metrics = (current.get("network_metrics") or {}) if isinstance(current, dict) else {}

    return {
        "baseline_run_id": baseline_run.get("run_id"),
        "current_run_id": current_run.get("run_id"),
        "metric_diffs": {
            "network_summary": diff_network_summary(
                baseline_metrics.get("network_summary"),
                current_metrics.get("network_summary"),
            ),
            "spof": diff_spof(
                baseline_metrics.get("spof"),
                current_metrics.get("spof"),
            ),
            "coverage_gaps": diff_coverage_gaps(
                baseline_metrics.get("coverage_gaps"),
                current_metrics.get("coverage_gaps"),
            ),
        },
    }


__all__ = [
    "diff_network_summary",
    "diff_spof",
    "diff_coverage_gaps",
    "diff_snapshots",
]
