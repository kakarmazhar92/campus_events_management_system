import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta
from utils.auth    import require_auth
from utils.queries import create_event, add_event_field, add_registration_field
from components.sidebar import render_sidebar
from components.navbar  import render_navbar
from components.cards   import page_header, section_title

# ── CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="CampusEvents Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.ui import load_css
load_css()

require_auth()
render_sidebar(active_page="Create Event")
render_navbar("Create Event")

page_header("Create", "New Event", "Configure event and dynamic fields")

# ── SESSION INIT ───────────────────────────────────
if "ce_ef_fields" not in st.session_state:
    st.session_state.ce_ef_fields = []

if "ce_rf_reg_fields" not in st.session_state:
    st.session_state.ce_rf_reg_fields = []

# ── FIELD BUILDERS (DYNAMIC) ───────────────────────
st.markdown("## 🧩 Configure Fields")

col1, col2 = st.columns(2)

# ── EVENT FIELDS ───────────────────────────────────
with col1:
    st.markdown("### Event Fields")

    ef_name = st.text_input("Field Name", key="ef_name")
    ef_type = st.selectbox("Type", ["text"], key="ef_type")

    if st.button("➕ Add Event Field"):
        if ef_name.strip():
            st.session_state.ce_ef_fields.append({
                "field_name": ef_name.strip(),
                "field_type": ef_type
            })
            st.rerun()

    # Show fields
    for i, f in enumerate(st.session_state.ce_ef_fields):
        c1, c2 = st.columns([4,1])
        c1.write(f"• {f['field_name']} ({f['field_type']})")
        if c2.button("❌", key=f"del_ef_{i}"):
            st.session_state.ce_ef_fields.pop(i)
            st.rerun()

# ── REGISTRATION FIELDS ────────────────────────────
with col2:
    st.markdown("### Registration Fields")

    rf_name = st.text_input("Field Name", key="rf_name")
    rf_type = st.selectbox("Type", ["text", "number", "date", "dropdown"], key="rf_type")

    # ✅ ADD THIS (missing part)
    rf_options = None
    if rf_type == "dropdown":
        rf_options = st.text_input(
            "Dropdown Options (comma separated)",
            key="rf_options",placeholder="CS, IT, ENTC"
        )

    if st.button("➕ Add Registration Field"):
        if rf_name.strip():

            # ✅ Validate dropdown options
            if rf_type == "dropdown" and not rf_options:
                st.error("Please enter dropdown options")
            else:
                st.session_state.ce_rf_reg_fields.append({
                    "field_name": rf_name.strip(),
                    "field_type": rf_type,
                    "is_required": 1,
                    "options": rf_options if rf_type == "dropdown" else None
                })
                st.rerun()

    # Show fields
    for i, f in enumerate(st.session_state.ce_rf_reg_fields):
        c1, c2 = st.columns([4,1])

        display = f"{f['field_name']} ({f['field_type']})"
        if f.get("options"):
            display += f" → [{f['options']}]"

        c1.write(f"• {display}")

        if c2.button("❌", key=f"del_rf_{i}"):
            st.session_state.ce_rf_reg_fields.pop(i)
            st.rerun()


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

    st.markdown("### 🧾 Selected Fields")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("**Event Fields:**")
        for f in st.session_state.ce_ef_fields:
            st.write(f"• {f['field_name']}")

    with colB:
        st.markdown("**Registration Fields:**")
        for f in st.session_state.ce_rf_reg_fields:
            st.write(f"• {f['field_name']}")

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

                event_id = create_event(
                    title=title,
                    description=description,
                    event_date=event_date,
                    image_url=image_url,
                    capacity=capacity,
                    deadline=deadline
                )

                # Save event fields
                for f in st.session_state.ce_ef_fields:
                    add_event_field(
                        event_id,
                        f["field_name"],
                        f["field_type"],
                        ""
                    )

                # Save registration fields
                for f in st.session_state.ce_rf_reg_fields:
                    add_registration_field(
                        event_id,
                        f["field_name"],
                        f["field_type"],
                        f["is_required"],
                        ""
                    )

                # Reset state
                st.session_state.ce_ef_fields = []
                st.session_state.ce_rf_reg_fields = []

                st.success("✅ Event created successfully!")
                st.balloons()

        except Exception as e:
            st.error(f"Error: {e}")