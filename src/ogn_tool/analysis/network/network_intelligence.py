import pandas as pd


def compute_network_topology(df: pd.DataFrame) -> dict:
    """
    Build a simple station-aircraft graph representation.

    Expected columns:
        lat, lon, ts_epoch, src (aircraft), igate (station)
    """

    nodes = set()
    edges = []

    for _, row in df.iterrows():
        aircraft = row["src"]
        station = row["igate"]

        nodes.add(("aircraft", aircraft))
        nodes.add(("station", station))

        edges.append({
            "source": station,
            "target": aircraft,
            "type": "reception"
        })

    return {
        "nodes": [{"id": n[1], "type": n[0]} for n in nodes],
        "edges": edges
    }


def compute_station_roles(df: pd.DataFrame) -> dict:
    """
    Classify stations based on packet volume.
    """

    counts = df.groupby("igate").size()

    roles = {}

    for station, packets in counts.items():

        if packets > 10000:
            role = "backbone"

        elif packets > 1000:
            role = "regional"

        else:
            role = "edge"

        roles[station] = {
            "packets": int(packets),
            "role": role
        }

    return roles


def compute_coverage_redundancy(df: pd.DataFrame, grid_size=0.1) -> pd.DataFrame:
    """
    Estimate redundancy of reception coverage.

    grid_size: degrees
    """

    df = df.copy()

    df["grid_lat"] = (df["lat"] / grid_size).round() * grid_size
    df["grid_lon"] = (df["lon"] / grid_size).round() * grid_size

    redundancy = (
        df.groupby(["grid_lat", "grid_lon"])["igate"]
        .nunique()
        .reset_index(name="stations")
    )

    return redundancy
