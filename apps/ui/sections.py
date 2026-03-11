from __future__ import annotations

from .pages.overview import render_overview_page
from .pages.rf_map import render_rf_map_page
from .pages.coverage_explorer import render_coverage_explorer_page
from .pages.propagation import render_propagation_page
from .pages.directional_rf import render_directional_rf_page
from .pages.terrain import render_terrain_page
from .pages.network import render_network_page
from .pages.diagnostics import render_diagnostics_page
from .pages.aircraft import render_aircraft_page
from .pages.coverage import render_coverage_page
from .pages.debug import render_debug_page
from .pages.station_intelligence import render_station_intelligence_page
from .pages.network_intelligence import render_network_intelligence


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
