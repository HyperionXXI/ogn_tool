from ogn_tool.domain.aircraft_observations import build_aircraft_observations, project_aircraft_positions


def test_build_aircraft_observations_aggregates_seen_by_within_time_window():
    packets = [
        {'src': 'A1', 'lat': 47.0, 'lon': 7.0, 'ts_epoch': 1000, 'igate': 'FK50887'},
        {'src': 'A1', 'lat': 47.0001, 'lon': 7.0001, 'ts_epoch': 1003, 'igate': 'LSPD'},
        {'src': 'A1', 'lat': 47.0002, 'lon': 7.0002, 'ts_epoch': 1015, 'igate': 'FK50887'},
    ]

    out = build_aircraft_observations(packets, temporal_threshold_s=10)

    assert len(out) == 2
    assert out[0]['aircraft_id'] == 'A1'
    assert out[0]['seen_by'] == ['FK50887', 'LSPD']


def test_project_aircraft_positions_keeps_projection_shape():
    observations = [
        {
            'aircraft_id': 'A1',
            'lat': 47.1,
            'lon': 7.2,
            'timestamp_epoch': 123,
            'seen_by': {'FK50887', 'LSPD'},
        }
    ]

    out = project_aircraft_positions(observations)

    assert len(out) == 1
    assert out[0]['src'] == 'A1'
    assert out[0]['lat'] == 47.1
    assert out[0]['lon'] == 7.2
    assert sorted(out[0]['seen_by']) == ['FK50887', 'LSPD']
