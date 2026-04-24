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

from utils.ui import load_css
load_css()

# Sidebar
st.sidebar.title("Admin Panel")
st.sidebar.markdown("---")
st.sidebar.write("Navigation")

# Always redirect to login first
st.switch_page("pages/login.py")
