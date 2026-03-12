import numpy as np

from ogn_tool.models.rf_feature_matrix import RFFeatureMatrix


def build_feature_matrix(observations):

    distance = np.array([o.distance_km for o in observations])
    bearing = np.array([o.bearing_deg for o in observations])
    altitude = np.array([o.altitude_m for o in observations])

    matrix = RFFeatureMatrix(
        azimuth=bearing,
        distance=distance,
        altitude=altitude,
        bearing=bearing,
        packet_count=int(len(observations)),
    )

    # Backward-compatible dynamic field used by existing antenna pattern logic.
    matrix.horizon = np.array([o.radio_horizon_km for o in observations])

    return matrix
