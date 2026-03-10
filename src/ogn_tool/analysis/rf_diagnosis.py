class RFDiagnosis:
    """
    RF diagnosis system for groundstation analysis.
    Converts RF metrics into human-readable explanations.
    """

    def __init__(self, metrics: dict, directional_balance: dict | None = None):
        self.metrics = metrics
        self.directional_balance = directional_balance

    def evaluate(self) -> list[str]:
        """Evaluate RF metrics and return detected issues."""

        issues = []

        rssi = self.metrics.get("rssi")
        noise = self.metrics.get("noise_floor")
        loss = self.metrics.get("packet_loss")

        if rssi is not None and rssi < -90:
            issues.append(f"Weak signal strength detected (RSSI={rssi} dBm).")

        if noise is not None and noise > -95:
            issues.append(f"Elevated noise floor detected (noise_floor={noise} dBm).")

        if loss is not None and loss > 0.1:
            issues.append(f"High packet loss detected ({loss*100:.1f}%).")

        if self.directional_balance and self.directional_balance.get("directional_bias"):
            issues.append("Directional reception imbalance detected.")

            weak_sectors = self.directional_balance.get("weak_sectors") or []
            if weak_sectors:
                issues.append(f"Weak reception sectors detected: {', '.join(weak_sectors)}")

        return issues

    def health_score(self) -> str:
        """Return station health classification."""

        if not self.metrics:
            return "UNKNOWN"

        issues = self.evaluate()

        if len(issues) == 0:
            return "GOOD"
        if len(issues) == 1:
            return "FAIR"

        return "POOR"
