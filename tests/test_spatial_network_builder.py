from ogn_tool.reporting.spatial_network_builder import build_spatial_network_features


def test_single_cell_aggregation_and_normalization():
    observations = [
        {
            'aircraft_id': 'A1',
            'lat': 47.0,
            'lon': 7.0,
            'timestamp_epoch': 100,
            'seen_by': ['FK50887'],
        },
        {
            'aircraft_id': 'A2',
            'lat': 47.0,
            'lon': 7.0,
            'timestamp_epoch': 110,
            'seen_by': ['FK50887', 'LSPD'],
        },
    ]

    out = build_spatial_network_features(observations, cell_size_km=2.5)

    assert out['grid_meta']['rows'] == 1
    assert out['grid_meta']['cols'] == 1
    assert out['coverage_density'][0]['value'] == 1.0
    assert 0.0 <= out['blind_zones'][0]['value'] <= 1.0
    assert out['grid_meta']['blind_semantics_version'] == 'a3'


def test_unique_vs_shared_separation_and_active_overlap_ratio():
    observations = [
        {
            'aircraft_id': 'A1',
            'lat': 47.0,
            'lon': 7.0,
            'timestamp_epoch': 100,
            'seen_by': ['FK50887'],
        },
        {
            'aircraft_id': 'A2',
            'lat': 47.03,
            'lon': 7.03,
            'timestamp_epoch': 110,
            'seen_by': ['FK50887', 'LSPD'],
        },
    ]

    out = build_spatial_network_features(observations, cell_size_km=2.0)

    unique_values = [cell['value'] for cell in out['unique_coverage']]
    shared_values = [cell['value'] for cell in out['shared_coverage']]

    assert max(unique_values) > 0.0
    assert max(shared_values) > 0.0
    assert 0.0 <= out['shared_overlap_ratio_active'] <= 1.0
    assert out['shared_overlap_ratio_active'] > 0.0


def test_normalization_bounds_for_all_layers():
    observations = [
        {
            'aircraft_id': 'A1',
            'lat': 47.0,
            'lon': 7.0,
            'timestamp_epoch': 100,
            'seen_by': ['S1'],
        },
        {
            'aircraft_id': 'A2',
            'lat': 47.02,
            'lon': 7.02,
            'timestamp_epoch': 120,
            'seen_by': ['S1', 'S2'],
        },
        {
            'aircraft_id': 'A3',
            'lat': 47.04,
            'lon': 7.04,
            'timestamp_epoch': 140,
            'seen_by': ['S1', 'S2', 'S3'],
        },
    ]

    out = build_spatial_network_features(observations, cell_size_km=2.0)

    for key in ('coverage_density', 'unique_coverage', 'shared_coverage', 'blind_zones', 'blind_actionable', 'blind_problematic'):
        for cell in out[key]:
            assert 0.0 <= cell['value'] <= 1.0
