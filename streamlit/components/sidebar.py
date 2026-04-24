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
    # ── Force sidebar open via JS (fixes the collapsed-on-rerun bug) ──────
    # Streamlit re-collapses the sidebar on every rerun when
    # initial_sidebar_state was ever "collapsed". This JS click
    # on the collapsed control button opens it if it's currently closed.
    st.markdown("""
    <script>
    (function() {
        function openSidebar() {
            // Target the collapsed-control button (the arrow tab on the left edge)
            var btn = window.parent.document.querySelector('[data-testid="collapsedControl"]');
            if (btn) {
                // Only click if sidebar is actually collapsed
                var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    var style = window.parent.getComputedStyle(sidebar);
                    // Sidebar is collapsed when its width is very small
                    if (parseInt(style.width) < 50) {
                        btn.click();
                    }
                }
            }
        }
        // Run after a short delay to let Streamlit render first
        setTimeout(openSidebar, 120);
    })();
    </script>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # ── Brand ────────────────────────────────────────────────────────
        st.markdown("""
        <div style="padding:1.2rem 0.75rem 1rem;
                    border-bottom:1px solid var(--border);
                    margin-bottom:1rem;">
            <div style="font-size:1.25rem;font-weight:700;color:var(--text-primary);
                        display:flex;align-items:center;gap:0.4rem;">
                🎓 <span style="color:var(--accent);">Campus</span>Events
            </div>
            <div style="font-size:0.68rem;color:var(--text-muted);margin-top:0.3rem;
                        letter-spacing:0.12em;text-transform:uppercase;">
                Admin Panel
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation ───────────────────────────────────────────────────
        st.markdown('<div class="section-title">Navigation</div>', unsafe_allow_html=True)

        for icon, label, path in NAV_ITEMS:
            is_active  = active_page == label
            btn_type   = "primary" if is_active else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{label}",
                use_container_width=True,
                type=btn_type,
            ):
                st.switch_page(path)

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # ── Admin info ───────────────────────────────────────────────────
        admin_user = st.session_state.get("admin_user", "admin")
        st.markdown(f"""
        <div style="padding:0.75rem 0.5rem 0.5rem;font-size:0.8rem;color:var(--text-muted);">
            Logged in as<br>
            <span style="color:var(--accent);font-weight:600;">{admin_user}</span>
        </div>
        """, unsafe_allow_html=True)

        render_logout_button()