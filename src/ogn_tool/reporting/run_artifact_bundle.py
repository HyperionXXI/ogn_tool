from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .network_engineering_report import NetworkEngineeringReport
from .network_engineering_report_builder import build_network_report_contract
from .report_export_io import export_network_report_json_file

BUNDLE_EXPORT_VERSION = '1.0'


def _try_write_ui_artifact(bundle_dir: Path) -> None:
    """Best-effort UI projection write; never fail bundle export."""
    try:
        from .ui_loader import write_ui_artifact

        write_ui_artifact(bundle_dir)
    except Exception:
        pass


def _write_additional_artifact(bundle_dir: Path, artifact_name: str, payload: Any) -> None:
    """Persist an additional JSON artifact inside the run bundle."""
    artifact_path = bundle_dir / f'{artifact_name}.json'
    with artifact_path.open('w', encoding='utf-8') as file_handle:
        json.dump(payload, file_handle, indent=2, sort_keys=True)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _extract_station_placement(report: NetworkEngineeringReport) -> dict[str, Any]:
    analysis_stats = report.analysis_stats if isinstance(report.analysis_stats, dict) else {}
    station_placement = analysis_stats.get('station_placement')
    if isinstance(station_placement, dict):
        return dict(station_placement)
    return {}


def _build_contract_metadata(
    *,
    bundle_version: str,
    generated_at: str,
    run_metadata: dict[str, Any],
    dataset_identity: dict[str, Any],
    comparability: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        'bundle_version': bundle_version,
        'generated_at': generated_at,
        'run': dict(run_metadata),
        'dataset': dict(dataset_identity),
    }
    if comparability is not None:
        metadata['comparability'] = dict(comparability)
    return metadata


def export_analysis_run_bundle(
    report: NetworkEngineeringReport,
    output_dir: str | Path,
    *,
    run_metadata: dict[str, Any] | None = None,
    dataset_identity: dict[str, Any] | None = None,
    comparability: dict[str, Any] | None = None,
    additional_artifacts: dict[str, Any] | None = None,
) -> Path:
    """Export a reproducible artifact bundle for a single analysis run."""
    _require(isinstance(report, NetworkEngineeringReport), 'report must be NetworkEngineeringReport')

    bundle_dir = Path(output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    generated_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec='seconds')
        .replace('+00:00', 'Z')
    )

    run_meta = dict(run_metadata or {})
    data_identity = dict(dataset_identity or {})

    _require(isinstance(report.network_summary, dict), 'report.network_summary must be a dict')
    _require(isinstance(report.station_health_table, pd.DataFrame), 'report.station_health_table must be a DataFrame')
    _require(isinstance(report.station_dependency, pd.DataFrame), 'report.station_dependency must be a DataFrame')
    _require(isinstance(report.network_redundancy, dict), 'report.network_redundancy must be a dict')

    coverage_score = report.network_summary.get('coverage_score')
    if coverage_score is not None and not isinstance(coverage_score, (int, float)):
        raise RuntimeError('report.network_summary.coverage_score must be numeric when provided')

    contract = build_network_report_contract(
        run_id=str(run_meta.get('run_id') or bundle_dir.name),
        metadata=_build_contract_metadata(
            bundle_version=BUNDLE_EXPORT_VERSION,
            generated_at=generated_at,
            run_metadata=run_meta,
            dataset_identity=data_identity,
            comparability=comparability,
        ),
        network_summary=report.network_summary,
        station_health=report.station_health_table,
        station_dependency=report.station_dependency,
        network_robustness=report.network_redundancy,
        station_placement=_extract_station_placement(report),
        coverage_score=None if coverage_score is None else float(coverage_score),
    )

    export_network_report_json_file(contract, bundle_dir / 'report.json')

    metadata_artifact = {
        'bundle_version': BUNDLE_EXPORT_VERSION,
        'generated_at': generated_at,
        'metadata': run_meta,
        'dataset': data_identity,
    }
    if comparability is not None:
        metadata_artifact['comparability'] = dict(comparability)
    with (bundle_dir / 'run_metadata.json').open('w', encoding='utf-8') as file_handle:
        json.dump(metadata_artifact, file_handle, indent=2, sort_keys=True)

    _try_write_ui_artifact(bundle_dir)

    for artifact_name, payload in (additional_artifacts or {}).items():
        _write_additional_artifact(bundle_dir, artifact_name, payload)

    return bundle_dir


__all__ = ['BUNDLE_EXPORT_VERSION', 'export_analysis_run_bundle']
