# components/sidebar.py

import streamlit as st
from components.navbar import render_logout_button


NAV_ITEMS = [
    ("📊", "Dashboard",     "pages/dashboard.py"),
    ("➕", "Create Event",  "pages/create_event.py"),
    ("📅", "Manage Events", "pages/manage_events.py"),
    ("👥", "Registrations", "pages/registrations.py"),
]


def render_sidebar(active_page: str = ""):
    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="padding:1.2rem 0.5rem 1rem;border-bottom:1px solid var(--border);margin-bottom:1rem;">
            <div style="font-size:1.3rem;font-weight:700;color:var(--text-primary);">
                🎓 <span style="color:var(--accent);">Campus</span>Events
            </div>
            <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.25rem;
                        letter-spacing:0.1em;text-transform:uppercase;">
                Admin Panel
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Navigation</div>', unsafe_allow_html=True)

        for icon, label, path in NAV_ITEMS:
            is_active = active_page == label
            btn_style = "primary" if is_active else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{label}",
                use_container_width=True,
                type=btn_style,
            ):
                st.switch_page(path)

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # Admin info
        admin_user = st.session_state.get("admin_user", "admin")
        st.markdown(f"""
        <div style="padding:0.75rem 0.5rem;font-size:0.8rem;color:var(--text-muted);">
            Logged in as<br>
            <span style="color:var(--accent);font-weight:600;">{admin_user}</span>
        </div>
        """, unsafe_allow_html=True)

        render_logout_button()
