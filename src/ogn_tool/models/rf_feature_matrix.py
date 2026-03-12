from dataclasses import dataclass

import numpy as np


@dataclass
class RFFeatureMatrix:

    azimuth: np.ndarray
    distance: np.ndarray
    altitude: np.ndarray
    bearing: np.ndarray

    packet_count: int
