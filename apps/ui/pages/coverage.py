from __future__ import annotations

import streamlit as st

from ogn_tool.ui.layout import DASHBOARD_COLUMNS
from apps.ui.metrics import metric_card
from ogn_tool.ui import charts as ui_charts
from ogn_tool.ui.charts import render_rf_cartography
from ogn_tool.rf_probability_field import build_rf_probability_field


def render_coverage_page(filters):
    ctx = filters
    dataset = ctx.get("dataset", {})
    # Late import to avoid circulars; reuse existing logic exactly.
    st.info("RF coverage map is available under the Infrastructure page.")

