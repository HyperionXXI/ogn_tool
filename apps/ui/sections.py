from __future__ import annotations

from .overview import render_overview_page
from apps.ui.pages.rf_map import render_rf_map_page
from .coverage_explorer import render_coverage_explorer_page
from apps.ui.pages.propagation import render_propagation_page
from apps.ui.pages.directional_rf import render_directional_rf_page
from apps.ui.pages.terrain import render_terrain_page
from apps.ui.pages.network import render_network_page
from apps.ui.pages.diagnostics import render_diagnostics_page
from apps.ui.pages.aircraft import render_aircraft_page
from apps.ui.pages.coverage import render_coverage_page
from apps.ui.pages.debug import render_debug_page
from apps.ui.pages.station_intelligence import render_station_intelligence_page
from apps.ui.pages.network_intelligence import render_network_intelligence


def render_overview_tab(ctx):
    return render_overview_page(ctx)


def render_rf_coverage_tab(ctx):
    return render_rf_map_page(ctx)


def render_coverage_explorer_tab(ctx):
    return render_coverage_explorer_page(ctx)


def render_aircraft_tab(ctx):
    return render_aircraft_page(ctx)


def render_coverage_tab(ctx):
    return render_coverage_page(ctx)


def render_network_tab(ctx):
    return render_network_page(ctx)


def render_diagnostics_tab(ctx):
    return render_diagnostics_page(ctx)


def render_signal_tab(ctx):
    return render_propagation_page(ctx)


def render_directional_rf_tab(ctx):
    return render_directional_rf_page(ctx)


def render_terrain_tab(ctx):
    return render_terrain_page(ctx)


def render_debug_tab(ctx):
    return render_debug_page(ctx)


def render_station_intelligence_tab(ctx):
    return render_station_intelligence_page(ctx)


def render_network_intelligence_tab(ctx):
    return render_network_intelligence(ctx)
