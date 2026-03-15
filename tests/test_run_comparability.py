from __future__ import annotations

from ogn_tool.reporting.run_comparability import build_run_comparability



def test_build_run_comparability_computes_duration() -> None:
    comparability = build_run_comparability(
        analysis_version='2026.03',
        time_window_start='2026-03-14T10:00:00Z',
        time_window_end='2026-03-14T11:00:00Z',
        config_identity='cfg_abc123',
    )

    assert comparability == {
        'schema_version': '1.0',
        'analysis_version': '2026.03',
        'time_window_start': '2026-03-14T10:00:00Z',
        'time_window_end': '2026-03-14T11:00:00Z',
        'time_window_duration_s': 3600,
        'config_identity': 'cfg_abc123',
    }



def test_build_run_comparability_handles_missing_window() -> None:
    comparability = build_run_comparability(
        analysis_version='2026.03',
        time_window_start=None,
        time_window_end=None,
        config_identity='cfg_abc123',
    )

    assert comparability['time_window_start'] is None
    assert comparability['time_window_end'] is None
    assert comparability['time_window_duration_s'] is None



def test_build_run_comparability_is_deterministic() -> None:
    first = build_run_comparability(
        analysis_version='2026.03',
        time_window_start='2026-03-14T10:00:00+01:00',
        time_window_end='2026-03-14T11:00:00+01:00',
        config_identity='cfg_abc123',
    )
    second = build_run_comparability(
        analysis_version='2026.03',
        time_window_start='2026-03-14T09:00:00Z',
        time_window_end='2026-03-14T10:00:00Z',
        config_identity='cfg_abc123',
    )

    assert first == second
