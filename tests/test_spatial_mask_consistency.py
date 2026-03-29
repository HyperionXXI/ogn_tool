from ogn_tool.reporting.spatial_network_builder import build_spatial_network_features


def _cell_key(row):
    return (round(float(row['lat']), 6), round(float(row['lon']), 6), round(float(row['value']), 6))


def test_blind_mask_consistency():
    observations = [
        {'aircraft_id': 'A1', 'lat': 47.00, 'lon': 7.00, 'timestamp_epoch': 100, 'seen_by': ['S1']},
        {'aircraft_id': 'A2', 'lat': 47.02, 'lon': 7.02, 'timestamp_epoch': 120, 'seen_by': ['S1', 'S2']},
        {'aircraft_id': 'A3', 'lat': 47.03, 'lon': 7.01, 'timestamp_epoch': 140, 'seen_by': ['S1']},
    ]

    out = build_spatial_network_features(observations, cell_size_km=2.0, analysis_radius_km=6.0)

    blind = {_cell_key(row) for row in out['blind_zones']}
    mask_coords = {(round(float(row['lat']), 6), round(float(row['lon']), 6)) for row in out['analysis_mask']}
    blind_masked = {_cell_key(row) for row in out['blind_zones_masked']}
    blind_actionable = {_cell_key(row) for row in out['blind_actionable']}
    blind_problematic = {_cell_key(row) for row in out['blind_problematic']}

    assert len(out['analysis_mask']) > 0
    assert len(out['blind_zones_masked']) > 0

    # blind_zones_masked ⊆ blind_zones
    assert blind_masked.issubset(blind)

    # blind_zones_masked ⊆ analysis_mask (by coordinates)
    for row in out['blind_zones_masked']:
        key = (round(float(row['lat']), 6), round(float(row['lon']), 6))
        assert key in mask_coords

    # blind_actionable ⊆ analysis_mask and ⊆ blind_zones
    assert blind_actionable.issubset(blind)
    for row in out['blind_actionable']:
        key = (round(float(row['lat']), 6), round(float(row['lon']), 6))
        assert key in mask_coords

    # blind_problematic ⊆ analysis_mask and ⊆ blind_zones
    assert blind_problematic.issubset(blind)
    for row in out['blind_problematic']:
        key = (round(float(row['lat']), 6), round(float(row['lon']), 6))
        assert key in mask_coords
