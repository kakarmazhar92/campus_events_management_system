# pages/login.py

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.auth  import login, seed_default_admin
from utils.helpers import load_css
from utils.db    import init_db, test_connection

st.set_page_config(
    page_title="Admin Login — CampusEvents",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load CSS
load_css()

# Init DB on first load
if "db_initialized" not in st.session_state:
    with st.spinner("Connecting to database…"):
        try:
            if init_db():
                seed_default_admin()
                st.session_state["db_initialized"] = True
            else:
                st.error("Database initialisation failed. Check your credentials.")
                st.stop()
        except ConnectionError as e:
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);
                        border-radius:12px;padding:1.5rem;margin-top:1rem;">
                <div style="color:#ef4444;font-weight:700;font-size:1rem;margin-bottom:0.75rem;">
                    ❌ Database Connection Failed
                </div>
                <div style="color:#a0a0a0;font-size:0.85rem;line-height:1.7;">
                    Cannot reach MySQL. Make sure:<br>
                    &nbsp;&nbsp;1. MySQL is running on your machine<br>
                    &nbsp;&nbsp;2. Your <code>.env</code> file exists with correct values<br>
                    &nbsp;&nbsp;3. The database <code>campus_events</code> has been created
                </div>
                <div style="margin-top:1rem;padding:0.75rem;background:#1a1a1a;
                            border-radius:6px;font-size:0.75rem;color:#f5b301;font-family:monospace;">
                    DB_HOST={os.getenv('DB_HOST','localhost')}<br>
                    DB_PORT={os.getenv('DB_PORT','3306')}<br>
                    DB_USER={os.getenv('DB_USER','root')}<br>
                    DB_NAME={os.getenv('DB_NAME','campus_events')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("📋 Error Details"):
                st.code(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.stop()

# Redirect if already logged in
if st.session_state.get("authenticated"):
    st.switch_page("pages/dashboard.py")

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:3rem 0 1.5rem;">
    <div style="font-size:2.5rem;margin-bottom:0.5rem;">🎓</div>
    <div style="font-size:1.6rem;font-weight:700;color:var(--text-primary);">
        Campus<span style="color:var(--accent);">Events</span>
    </div>
    <div style="font-size:0.8rem;color:var(--text-muted);letter-spacing:0.1em;
                text-transform:uppercase;margin-top:0.3rem;">
        Admin Portal
    </div>
</div>
""", unsafe_allow_html=True)

with st.form("login_form", clear_on_submit=False):
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:2.5rem 2rem;max-width:400px;
                margin:0 auto;">
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:1rem;font-weight:600;margin-bottom:1.5rem;color:var(--text-primary);">Sign in to your account</div>',
                unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="admin", key="login_username")
    password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Sign In →", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            with st.spinner("Authenticating…"):
                if login(username, password):
                    st.success("Login successful! Redirecting…")
                    st.switch_page("pages/dashboard.py")
                else:
                    st.error("Invalid username or password.")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;margin-top:2rem;font-size:0.75rem;color:var(--text-muted);">
    Default credentials: <code style="color:var(--accent);">admin / admin123</code>
    &nbsp;·&nbsp; Change after first login
</div>
""", unsafe_allow_html=True)

# DB status indicator
if test_connection():
    st.markdown('<div style="text-align:center;margin-top:1rem;font-size:0.7rem;color:var(--success);">⬤ Database connected</div>',
                unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center;margin-top:1rem;font-size:0.7rem;color:var(--error);">⬤ Database offline</div>',
                unsafe_allow_html=True)