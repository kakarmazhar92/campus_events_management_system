import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta
from utils.auth    import require_auth
from utils.queries import create_event
from components.sidebar import render_sidebar
from components.navbar  import render_navbar
from components.cards   import page_header

# ── CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="CampusEvents Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
css_path = os.path.join(BASE_DIR, "assets", "styles.css")

with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

require_auth()
render_sidebar(active_page="Create Event")
render_navbar("Create Event")

page_header("Create", "New Event", "Create event easily")

st.divider()

# ── MAIN FORM ──────────────────────────────────────
with st.form("create_event_form"):

    st.markdown("## 📌 Event Details")

    c1, c2 = st.columns([2,1])

    with c1:
        title = st.text_input("Event Title *")
    with c2:
        capacity = st.number_input("Capacity", min_value=1, value=100)

    description = st.text_area("Description")

    c3, c4, c5 = st.columns(3)

    with c3:
        event_date = st.date_input("Event Date", value=date.today() + timedelta(days=7))
    with c4:
        deadline = st.date_input("Deadline", value=date.today() + timedelta(days=5))
    with c5:
        image_url = st.text_input("Image URL")

    submit = st.form_submit_button("🚀 Create Event")


# ── SUBMIT LOGIC ───────────────────────────────────
if submit:

    errors = []

    if not title.strip():
        errors.append("Title required")

    if deadline > event_date:
        errors.append("Deadline must be before event date")

    if errors:
        for e in errors:
            st.error(e)

    else:
        try:
            with st.spinner("Creating event..."):

                create_event(
                    title=title.strip(),
                    description=description,
                    event_date=event_date,
                    image_url=image_url,
                    capacity=capacity,
                    deadline=deadline
                )

                st.success("✅ Event created successfully!")
                st.balloons()

        except Exception as e:
            st.error(f"Error: {e}")