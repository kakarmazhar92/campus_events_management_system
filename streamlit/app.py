# app.py — Entry point

import streamlit as st

st.set_page_config(
    page_title="CampusEvents Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Always redirect to login first
st.switch_page("pages/login.py")
