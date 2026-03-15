from __future__ import annotations

from ogn_tool.analysis.dataset_identity import build_dataset_identity



def test_build_dataset_identity_is_deterministic() -> None:
    first = build_dataset_identity(100, '2026-03-14T10:00:00Z', '2026-03-14T11:00:00Z', 'ogn_sqlite')
    second = build_dataset_identity(100, '2026-03-14T10:00:00Z', '2026-03-14T11:00:00Z', 'ogn_sqlite')

    assert first == second



def test_build_dataset_identity_changes_with_packet_count() -> None:
    first = build_dataset_identity(100, '2026-03-14T10:00:00Z', '2026-03-14T11:00:00Z', 'ogn_sqlite')
    second = build_dataset_identity(101, '2026-03-14T10:00:00Z', '2026-03-14T11:00:00Z', 'ogn_sqlite')

    assert first['dataset_id'] != second['dataset_id']



def test_build_dataset_identity_changes_with_time_range() -> None:
    first = build_dataset_identity(100, '2026-03-14T10:00:00Z', '2026-03-14T11:00:00Z', 'ogn_sqlite')
    second = build_dataset_identity(100, '2026-03-14T10:30:00Z', '2026-03-14T11:00:00Z', 'ogn_sqlite')

    assert first['dataset_id'] != second['dataset_id']
