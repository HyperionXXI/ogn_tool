from __future__ import annotations

import streamlit as st



def render_coverage_page(filters):
    ctx = filters
    results = ctx.get("results")
    if results is not None and getattr(results, "coverage", None) is not None:
        st.info("RF coverage map is available under the Infrastructure page.")
    else:
        st.info("RF coverage map is available under the Infrastructure page.")




