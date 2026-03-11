import numpy as np


def build_feature_matrix(observations):

    distance = np.array([o.distance_km for o in observations])
    bearing = np.array([o.bearing_deg for o in observations])
    horizon = np.array([o.radio_horizon_km for o in observations])

    return {
        "distance": distance,
        "bearing": bearing,
        "horizon": horizon
    }
