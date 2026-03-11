STATUS: derived
REFERENCE: docs/ROADMAP_MASTER.md

# RF Pipeline Reproducibility

Run the RF analysis pipeline on the reference dataset.

Command:

```bash
PYTHONPATH=src python scripts/run_rf_analysis.py \
  --packets tests/data/sample_packets.csv \
  --station-lat 47.3359 \
  --station-lon 7.2728 \
  --out-dir tmp_out
```

Expected output:

```
tmp_out/
    coverage.csv
    propagation.csv
    metrics.json
```

Compare with reference:

```
tests/reference_output/
```
