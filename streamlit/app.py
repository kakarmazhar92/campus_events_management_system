# app.py — Entry point

import streamlit as st
import os

st.set_page_config(
    page_title="CampusEvents Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Config
st.set_page_config(
    page_title="Admin Panel",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Always redirect to login first
st.switch_page("pages/login.py")
