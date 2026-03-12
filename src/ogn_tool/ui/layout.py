import streamlit as st

DASHBOARD_COLUMNS = 5


def five_columns():
    return st.columns(DASHBOARD_COLUMNS)


def divider() -> None:
    st.divider()
