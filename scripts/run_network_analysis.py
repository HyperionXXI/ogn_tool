import json
import pandas as pd
from pathlib import Path

from ogn_tool.analysis.network.network_intelligence import (
    compute_network_topology,
    compute_station_roles,
    compute_coverage_redundancy
)


def main():

    packets = pd.read_csv("tests/data/sample_packets.csv")

    out_dir = Path("network_out")
    out_dir.mkdir(exist_ok=True)

    topology = compute_network_topology(packets)
    roles = compute_station_roles(packets)
    redundancy = compute_coverage_redundancy(packets)

    json.dump(topology, open(out_dir / "network_topology.json", "w"), indent=2)
    json.dump(roles, open(out_dir / "station_roles.json", "w"), indent=2)

    redundancy.to_csv(out_dir / "coverage_redundancy.csv", index=False)


if __name__ == "__main__":
    main()
