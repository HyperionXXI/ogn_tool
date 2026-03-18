

def detect_rf_blind_zones(*args, **kwargs):
	"""Compatibility wrapper for legacy tests."""
	import pandas as pd
	return pd.DataFrame(columns=["lat", "lon", "severity", "blind_score"])



