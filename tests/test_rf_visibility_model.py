from ogn_tool.analysis.rf_models.rf_visibility_model import compute_radio_horizon


def test_radio_horizon():
    res = compute_radio_horizon(10, 1200)
    assert 130 <= res["radio_horizon_km"] <= 150

