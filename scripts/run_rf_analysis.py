from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ogn_tool.engine.rf_engine import RFAnalysisEngine
from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset


def main():
    parser = argparse.ArgumentParser(description="Run RF analysis engine on a packets CSV.")
    parser.add_argument("--packets", required=True, help="Path to packets CSV")
    parser.add_argument("--station-lat", type=float, required=True)
    parser.add_argument("--station-lon", type=float, required=True)
    parser.add_argument("--out-dir", default=".", help="Output directory")
    args = parser.parse_args()

    packets = pd.read_csv(args.packets)
    engine = RFAnalysisEngine(packets, args.station_lat, args.station_lon)
    result = engine.run(RFAnalysisDataset(observations=[]))

    from ogn_tool.analytics.rf.rf_analysis_report import build_rf_analysis_report, export_rf_analysis_report
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_rf_analysis_report(result)
    export_rf_analysis_report(report, str(out_dir))
    # Optionally keep legacy outputs for compatibility
    coverage_df = result.coverage if isinstance(result.coverage, pd.DataFrame) else pd.DataFrame()
    propagation_df = (result.metrics or {}).get("distance_df")
    if not isinstance(propagation_df, pd.DataFrame):
        propagation_df = pd.DataFrame()
    coverage_df.to_csv(out_dir / "coverage.csv", index=False)
    propagation_df.to_csv(out_dir / "propagation.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(result.metrics or {}, f, indent=2, default=str)


if __name__ == "__main__":
    main()
