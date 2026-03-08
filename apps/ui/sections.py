from __future__ import annotations

from .pages.overview import render_overview_page
from .pages.rf_map import render_rf_map_page
from .pages.propagation import render_propagation_page
from .pages.directional_rf import render_directional_rf_page, render_legacy_rf_page
from .pages.terrain import render_terrain_page
from .pages.network import render_network_page
from .pages.diagnostics import render_diagnostics_page
from .pages.aircraft import render_aircraft_page
from .pages.coverage import render_coverage_page
from .pages.debug import render_debug_page


def render_coverage_tab(filters):
    return render_coverage_page(filters)


def render_overview_tab(ctx):
    return render_overview_page(ctx)


def render_rf_coverage_tab(ctx):
    return render_rf_map_page(ctx)


def render_aircraft_tab(ctx):
    return render_aircraft_page(ctx)


def render_network_tab(ctx):
    return render_network_page(ctx)


def render_diagnostics_tab(ctx):
    return render_diagnostics_page(ctx)


def render_signal_tab(filters):
    return render_propagation_page(filters)


def render_directional_rf_tab(ctx):
    return render_directional_rf_page(ctx)


def render_terrain_tab(ctx):
    return render_terrain_page(ctx)


def render_rf_tab(filters):
    return render_legacy_rf_page(filters)


def render_debug_tab(filters):
    return render_debug_page(filters)
