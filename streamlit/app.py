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

# Load CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets/styles.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Sidebar
st.sidebar.title("Admin Panel")
st.sidebar.markdown("---")
st.sidebar.write("Navigation")

# Always redirect to login first
st.switch_page("pages/login.py")
