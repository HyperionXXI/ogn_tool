from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ogn_tool.reporting import build_directional_summary, format_directional_summary


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> None:
    parser = argparse.ArgumentParser(description='Summarize FK50887 directional artifacts for human reading')
    parser.add_argument('run_dir', type=Path, help='Directional artifact directory under analysis_directional/')
    args = parser.parse_args()

    run_dir = args.run_dir
    histogram = _load_json(run_dir / 'azimuth_histogram.json') or {}
    directional_balance = _load_json(run_dir / 'directional_balance.json')
    station_angular_entropy = _load_json(run_dir / 'station_angular_entropy.json')
    shadow_risk_scores = _load_json(run_dir / 'shadow_risk_scores.json')

    summary = build_directional_summary(
        histogram,
        directional_balance,
        run_id=run_dir.name,
        station_angular_entropy=station_angular_entropy,
        shadow_risk_scores=shadow_risk_scores,
    )
    output_path = run_dir / 'directional_summary.json'
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8')

    print(format_directional_summary(summary))
    print(f'Written: {output_path}')


if __name__ == '__main__':
    main()
