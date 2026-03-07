import streamlit as st

DASHBOARD_COLUMNS = 5


def five_columns():
    return st.columns(DASHBOARD_COLUMNS)


def section_header(title: str) -> None:
    st.subheader(title)


def divider() -> None:
    st.divider()
