# components/navbar.py

import streamlit as st
from utils.auth import logout


def render_navbar(page_title: str = "Dashboard"):
    admin = st.session_state.get("admin_user", "Admin")

    st.markdown(f"""
    <div class="top-navbar">
        <div class="navbar-brand">
            🎓 <span>Campus</span>Events &nbsp;
            <span style="color:var(--text-muted);font-weight:400;font-size:0.8rem">/ {page_title}</span>
        </div>
        <div class="navbar-user">
            <span style="color:var(--accent);">⬤</span> &nbsp; {admin}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_logout_button():
    if st.sidebar.button("🚪 Logout", use_container_width=True, type="secondary"):
        logout()
        st.switch_page("pages/login.py")
