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


