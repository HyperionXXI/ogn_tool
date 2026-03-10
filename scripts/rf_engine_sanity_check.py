import os
import sys
import sqlite3

import pandas as pd

# Ensure the `src` folder is on sys.path so `ogn_tool` can be imported
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from ogn_tool.engine.rf_engine import RFAnalysisEngine


DB_PATH = r"F:\Data\ogn\ogn_log.sqlite3"


def load_packets(limit=20000):
    con = sqlite3.connect(DB_PATH)
    query = f"""
    SELECT
        lat,
        lon,
        NULL AS alt,
        ts_epoch,
        src,
        src AS aircraft,
        igate
    FROM packets
    WHERE lat IS NOT NULL
      AND lon IS NOT NULL
      AND igate IS NOT NULL
    LIMIT {limit}
    """

    df = pd.read_sql_query(query, con)
    con.close()
    return df


def main():
    print("Loading packets...")
    df = load_packets()
    print("Packets loaded:", len(df))

    # Ensure required columns exist for the analysis pipeline
    if "src" in df.columns and "aircraft" not in df.columns:
        df["aircraft"] = df["src"]

    station_lat = 47.33
    station_lon = 7.27

    print("Initializing RFAnalysisEngine...")
    engine = RFAnalysisEngine(
        df,
        station_lat=station_lat,
        station_lon=station_lon,
    )

    print("Building RF dataset...")
    dataset = engine.build_analysis_dataset()

    print("\n--- RF PIPELINE DEBUG ---")
    print("packets_all:", len(dataset["packets_all"]))
    print("packets_rf:", len(dataset["packets_rf"]))
    print("packets_filtered:", len(dataset["packets_filtered"]))

    if dataset["coverage_grid"] is not None:
        print("coverage_grid rows:", len(dataset["coverage_grid"]))
    else:
        print("coverage_grid: None")

    if dataset["azimuth_histogram"] is not None:
        print("azimuth bins:", len(dataset["azimuth_histogram"]))
    else:
        print("azimuth_histogram: None")

    print("\nStations detected:", len(dataset.get("stations", [])))

    print("\nSample RF packet:")
    if len(dataset["packets_rf"]) > 0:
        print(dataset["packets_rf"].iloc[0].to_dict())
    else:
        print("No RF packets generated")

    print("\nDataset keys:")
    print(list(dataset.keys()))

    print("\nObservations:", len(dataset["observations"]))

    print("\n--- RF ANALYSIS ---")

    if dataset["azimuth_histogram"] is not None:
        print("Azimuth bins:", len(dataset["azimuth_histogram"]))

    if dataset["directional_balance"]:
        print("Directional bias:", dataset["directional_balance"].get("directional_bias"))
        print("Weak sectors:", dataset["directional_balance"].get("weak_sectors"))

    if dataset["shadow_map"]:
        print("Shadow sectors:", dataset["shadow_map"].get("shadow_sectors"))

    if dataset["network_blind_zones"]:
        print("Blind zones:", len(dataset["network_blind_zones"].get("blind_zones", [])))

    if dataset["coverage_grid"] is not None:
        print("Coverage cells:", len(dataset["coverage_grid"]))

    if dataset["azimuth_histogram"] is not None:
        print("Azimuth bins:", len(dataset["azimuth_histogram"]))

    if dataset["directional_balance"] is not None:
        print("Directional bias:", dataset["directional_balance"]["directional_bias"])

    if dataset["shadow_map"]:
        print("Shadow sectors:", dataset["shadow_map"]["shadow_sectors"])

    if dataset["network_blind_zones"]:
        print("Blind zones:", len(dataset["network_blind_zones"]["blind_zones"]))

    assert dataset["observations"] is not None
    assert len(dataset["observations"]) > 0

    assert "station_metrics" in dataset
    assert "network_metrics" in dataset

    print("\n--- RF ENGINE DIAGNOSTIC SUMMARY ---")

    obs = len(dataset["observations"])
    cells = len(dataset["coverage_grid"]) if dataset["coverage_grid"] is not None else 0
    az = len(dataset["azimuth_histogram"]) if dataset["azimuth_histogram"] is not None else 0

    print(f"Observations: {obs}")
    print(f"Coverage cells: {cells}")
    print(f"Azimuth bins: {az}")

    if dataset["directional_balance"]:
        print("Directional bias:", dataset["directional_balance"].get("directional_bias"))

    if dataset["shadow_map"]:
        print("Shadow sectors:", dataset["shadow_map"].get("shadow_sectors"))

    if dataset["network_blind_zones"]:
        print(
            "Blind zones:",
            len(dataset["network_blind_zones"].get("blind_zones", [])),
        )

    print("\nSanity check completed.")


if __name__ == "__main__":
    main()
