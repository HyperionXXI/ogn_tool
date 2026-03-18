import numpy as np

from ogn_tool.models.rf_feature_matrix import RFFeatureMatrix


def build_feature_matrix(observations):

    vectors = observations
    if isinstance(observations, dict):
        vectors = observations.get("vectors")

    if isinstance(vectors, list):
        distance = np.array([o.distance_km for o in vectors])
        bearing = np.array([o.bearing_deg for o in vectors])
        altitude = np.array([o.altitude_m for o in vectors])
        horizon = np.array([o.radio_horizon_km for o in vectors])
        packet_count = int(len(vectors))
    else:
        df = observations.get("distance_df") if isinstance(observations, dict) else None
        if df is None:
            df = []
        distance = np.array(getattr(df, "get", lambda *_: [])("distance_km", []))
        bearing = np.array(getattr(df, "get", lambda *_: [])("bearing_deg", []))
        altitude = np.array(getattr(df, "get", lambda *_: [])("altitude_m", []))
        horizon = np.array(getattr(df, "get", lambda *_: [])("radio_horizon_km", []))
        packet_count = int(len(distance))

    matrix = RFFeatureMatrix(
        azimuth=bearing,
        distance=distance,
        altitude=altitude,
        bearing=bearing,
        packet_count=packet_count,
    )

    # Backward-compatible dynamic field used by existing antenna pattern logic.
    matrix.horizon = horizon

    return matrix
