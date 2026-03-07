import streamlit as st


def no_data_message() -> None:
    st.info(
        "No packets detected in this time window. "
        "Try increasing the time window or disabling filters."
    )
