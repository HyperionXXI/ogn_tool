STATUS: derived
REFERENCE: docs/core/ROADMAP_MASTER.md

# RF Diagnosis Layer

## Purpose

The RF diagnosis layer is a lightweight analysis framework designed to interpret RF metrics computed by the system and translate them into human-readable diagnostics. It serves as an additional analysis layer that can highlight potential issues or observations in groundstation RF performance without modifying the core RF engine or dashboard logic.

## Input metrics

The diagnosis framework consumes a dictionary of metrics gathered from RF analysis, such as signal strength, noise floor, link quality, station geometry, or other derived RF quantities. The specific metric keys and values are implementation-dependent and may evolve over time.

## Output diagnostics

The output of the diagnosis layer is a list of textual findings or issues detected in the input metrics. This can include:

- Identified problems (e.g., low signal, unusual noise, unexpected attenuation)
- Suggestions for further investigation (e.g., check antenna alignment, verify obstructions)
- Health classification labels (e.g., GOOD, FAIR, POOR, UNKNOWN)

## Examples

### Example 1: Basic usage

1. Collect RF metrics from an analysis run.
2. Instantiate the diagnosis system with the metrics.
3. Call `evaluate()` to get a list of detected issues.
4. Call `health_score()` to retrieve a high-level health classification.

```python
from ogn_tool.analysis.rf_diagnosis import RFDiagnosis

metrics = {
    "rssi": -85,
    "noise_floor": -110,
    "packet_loss": 0.03,
}

diagnosis = RFDiagnosis(metrics)
issues = diagnosis.evaluate()
health = diagnosis.health_score()

print("Issues:", issues)
print("Health:", health)
```

### Example 2: Interpreting results

A future implementation may produce output such as:

- `"Weak signal strength detected (RSSI=-85 dBm)."`
- `"Elevated noise floor suggests local interference."`
- `"Health classification: FAIR"`

