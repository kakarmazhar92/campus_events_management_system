import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta
from utils.auth    import require_auth
from utils.queries import create_event, add_event_field, add_registration_field
from components.sidebar import render_sidebar
from components.navbar  import render_navbar
from components.cards   import page_header, section_title

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# ── CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="Create_Event — CampusEvents",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
css_path = os.path.join(BASE_DIR, "assets", "styles.css")

custom_css = ""

# load your css safely
if os.path.exists(css_path):
    with open(css_path) as f:
        custom_css = f.read()

# FORCE SIDEBAR ALWAYS OPEN (HARD LOCK)
custom_css += """
/* Disable collapse completely */
[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 260px !important;
    max-width: 260px !important;
    transform: translateX(0px) !important;
}

/* Keep sidebar always visible */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    min-width: 260px !important;
    max-width: 260px !important;
}

/* Hide toggle button completely */
button[title="Toggle sidebar"] {
    display: none !important;
}

/* Prevent content shifting */
section.main {
    margin-left: 260px !important;
}

/* Mobile fix */
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 200px !important;
    }
    section.main {
        margin-left: 200px !important;
    }
}
"""

st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

require_auth()
render_sidebar(active_page="Create Event")
render_navbar("Create Event")

page_header("Create", "New Event", "Configure event and dynamic fields")

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
        if "uploaded_image_url" not in st.session_state:
            st.session_state.uploaded_image_url = ""

        uploaded_file = st.file_uploader("Upload Event Image", type=["jpg","png","jpeg"])

        if uploaded_file and not st.session_state.uploaded_image_url:
            result = cloudinary.uploader.upload(uploaded_file)
            st.session_state.uploaded_image_url = result["secure_url"]
            st.success("Uploaded ✅")

        if st.session_state.uploaded_image_url:
            st.image(st.session_state.uploaded_image_url, use_container_width=True)

        image_url = st.session_state.uploaded_image_url or \
            "https://via.placeholder.com/400x200?text=Event"

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

                # ✅ properly inside spinner
                event_id = create_event(
                    title=title,
                    description=description,
                    event_date=event_date,
                    image_url=image_url,
                    capacity=capacity,
                    deadline=deadline
                )

                # ✅ reset uploaded image
                st.session_state.uploaded_image_url = ""

                # ✅ success UI
                st.success("✅ Event created successfully!")
                st.balloons()

        except Exception as e:
            st.error(f"Error: {e}")