from __future__ import annotations

from ogn_tool.rf import signal_distance as signal_distance_model
from ogn_tool.core.rf_models_api import (
    altitude_distance_model,
    radio_horizon_model,
    terrain_model,
    terrain_visibility_model,
)

MODELS = {
    "signal_distance": signal_distance_model.analyze,
    "altitude_distance": altitude_distance_model.analyze,
    "radio_horizon": radio_horizon_model.analyze,
    "terrain": terrain_model.analyze,
    "terrain_visibility": terrain_visibility_model.analyze,
}


