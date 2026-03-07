import streamlit as st

from .layout import five_columns


def metric_card(col_or_label, label=None, value=None) -> None:
    """
    Render a metric with a uniform trailing spacer for consistent height.
    Accepts either (col, label, value) or (label, value) inside a column context.
    """
    if value is None and label is not None:
        st.metric(col_or_label, label)
        st.write("")
        return
    if value is None and label is None:
        return
    col = col_or_label
    col.metric(label, value)
    col.write("")


def render_kpi_row(packets, reliable_distance, max_distance, grid_cells, p95_distance) -> None:
    c1, c2, c3, c4, c5 = five_columns()
    metric_card(c1, "Packets in window", packets)
    metric_card(c2, "Reliable distance", reliable_distance)
    metric_card(c3, "Max distance", max_distance)
    metric_card(c4, "Grid cells", grid_cells)
    metric_card(c5, "P95 distance", p95_distance)
