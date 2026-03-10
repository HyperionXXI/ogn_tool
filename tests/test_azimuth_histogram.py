import numpy as np
from ogn_tool.analysis.azimuth import compute_azimuth_histogram


def test_azimuth_histogram_has_36_bins():
    bearings = np.random.uniform(0, 360, 1000)

    hist = compute_azimuth_histogram(bearings)

    assert hist is not None
    assert len(hist) == 36

    for sector in hist:
        assert "azimuth_start" in sector
        assert "azimuth_end" in sector
        assert "packet_count" in sector
