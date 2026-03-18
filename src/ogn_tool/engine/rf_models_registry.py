from __future__ import annotations

from ogn_tool.rf import signal_distance as signal_distance_model
from ogn_tool.analysis.rf_models import altitude_distance as altitude_distance_model
from ogn_tool.analysis.rf_models import radio_horizon as radio_horizon_model
from ogn_tool.analysis.rf_models import terrain as terrain_model
from ogn_tool.analysis.rf_models import terrain_visibility as terrain_visibility_model

MODELS = {
    "signal_distance": signal_distance_model.analyze,
    "altitude_distance": altitude_distance_model.analyze,
    "radio_horizon": radio_horizon_model.analyze,
    "terrain": terrain_model.analyze,
    "terrain_visibility": terrain_visibility_model.analyze,
}


