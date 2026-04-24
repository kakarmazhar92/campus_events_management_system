# utils/helpers.py
import streamlit as st
from pathlib import Path

def load_css():
    """Absolute-path CSS loader. Works on localhost, Streamlit Cloud, Render, anywhere."""
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if not css_path.exists():
        st.warning(f"styles.css not found at: {css_path}")
        return
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)