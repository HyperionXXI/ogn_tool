from __future__ import annotations

from ogn_tool.rf import signal_distance as analysis_signal_distance
from ogn_tool.analysis.rf_models import altitude_distance as analysis_altitude_distance
from ogn_tool.analysis.rf_models import radio_horizon as analysis_radio_horizon
from ogn_tool.analysis.rf_models import terrain as analysis_terrain
from ogn_tool.analysis.rf_models import terrain_visibility as analysis_terrain_visibility

MODELS = {
    "signal_distance": analysis_signal_distance.analyze,
    "altitude_distance": analysis_altitude_distance.analyze,
    "radio_horizon": analysis_radio_horizon.analyze,
    "terrain": analysis_terrain.analyze,
    "terrain_visibility": analysis_terrain_visibility.analyze,
}


