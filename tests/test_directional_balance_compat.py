from ogn_tool.analysis.azimuth import analyze_directional_balance


def test_directional_balance_new_format():
    sectors = [
        {"azimuth_start": i * 10, "azimuth_end": (i + 1) * 10, "packet_count": 10}
        for i in range(36)
    ]

    result = analyze_directional_balance(sectors)

    assert "directional_bias" in result
    assert "weak_sectors" in result
    assert "strong_sectors" in result


def test_directional_balance_legacy_format():
    hist = [10] * 36
    edges = list(range(0, 361, 10))

    legacy = {
        "hist": hist,
        "edges": edges,
    }

    result = analyze_directional_balance(legacy)

    assert "directional_bias" in result
