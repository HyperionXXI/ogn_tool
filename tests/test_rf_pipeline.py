import subprocess
import json
import os


def test_rf_pipeline(tmp_path):

    out_dir = tmp_path / "rf_out"

    env = dict(**os.environ)
    env["PYTHONPATH"] = "src"

    subprocess.run([
        "python",
        "scripts/run_rf_analysis.py",
        "--packets", "tests/data/sample_packets.csv",
        "--station-lat", "47.3359",
        "--station-lon", "7.2728",
        "--out-dir", str(out_dir)
    ], check=True, env=env)

    metrics = json.load(open(out_dir / "metrics.json"))
    ref = json.load(open("tests/reference_output/metrics.json"))

    assert metrics["rf_packets"] == ref["rf_packets"]
