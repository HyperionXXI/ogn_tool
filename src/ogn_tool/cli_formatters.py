"""Text formatters for thin CLI consumers of the reporting layer."""

from __future__ import annotations

from typing import Any


def format_latest_run(run: dict[str, Any] | None) -> str:
    """Format the latest run summary for terminal output."""
    if not run:
        return 'No runs available.'

    return "\n".join([
        'Latest run',
        '----------',
        f"Run ID: {run.get('run_id')}",
        f"Generated at: {run.get('generated_at')}",
        f"Path: {run.get('path')}",
        f"Bundle version: {run.get('bundle_version')}",
    ])


def format_run_comparison(result: dict[str, Any]) -> str:
    """Format a run comparison result for terminal output."""
    comparability = result.get('comparability', {}) if isinstance(result, dict) else {}
    interpretation = result.get('interpretation', {}) if isinstance(result, dict) else {}
    summary_delta = result.get('summary_delta', {}) if isinstance(result, dict) else {}

    lines = [
        'Run comparison',
        '--------------',
        f"Comparable: {comparability.get('is_comparable')}",
        f"Trend: {interpretation.get('network_trend', 'unknown')}",
    ]

    redundancy_value = summary_delta.get('redundancy_score')
    redundancy = redundancy_value if isinstance(redundancy_value, dict) else {}
    critical_value = summary_delta.get('critical_station_count')
    critical = critical_value if isinstance(critical_value, dict) else {}

    lines.append(f"Redundancy delta: {float(redundancy.get('delta') or 0.0):+.3f}")
    lines.append(f"Critical station delta: {float(critical.get('delta') or 0.0):+.0f}")

    main_changes = interpretation.get('main_changes', []) if isinstance(interpretation.get('main_changes'), list) else []
    if main_changes:
        lines.append('Main changes:')
        lines.extend(f"- {item}" for item in main_changes)

    return "\n".join(lines)


def format_network_evolution(result: dict[str, Any]) -> str:
    """Format a network evolution view for terminal output."""
    lineage = result.get('lineage', {}) if isinstance(result, dict) else {}
    trend = result.get('trend', {}) if isinstance(result, dict) else {}
    events = result.get('events', []) if isinstance(result, dict) else []
    runs = result.get('runs', []) if isinstance(result, dict) else []

    lines = [
        'Network evolution',
        '-----------------',
        f"Runs analyzed: {len(runs)}",
        f"Lineage consistent: {lineage.get('consistent')}",
        f"Redundancy trend: {trend.get('network_redundancy', 'unknown')}",
        f"Health trend: {trend.get('network_health', 'unknown')}",
    ]

    if events:
        lines.append('Events:')
        for event in events:
            lines.append(f"- {event.get('type')} in {event.get('run')}")

    return "\n".join(lines)


__all__ = ['format_latest_run', 'format_run_comparison', 'format_network_evolution']
