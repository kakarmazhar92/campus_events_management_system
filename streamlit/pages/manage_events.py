# pages/manage_events.py

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from utils.auth    import require_auth
from utils.queries import (
    get_all_events, get_event_by_id, update_event, delete_event,
    get_event_fields, get_registration_fields,
    add_event_field, delete_event_field,
    add_registration_field, delete_registration_field,
)
from components.sidebar import render_sidebar
from components.navbar  import render_navbar
from components.cards   import page_header, section_title, empty_state, event_card
from components.forms   import render_event_field_builder, render_registration_field_builder

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Manage Events — CampusEvents",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

require_auth()
render_sidebar(active_page="Manage Events")
render_navbar("Manage Events")

page_header("Manage", "Events", "View, edit and delete campus events")

# ── FILTER BAR ────────────────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns([3, 2, 1])
with fc1:
    search_q = st.text_input("🔍 Search events", placeholder="Type to search by title…",
                              key="me_search", label_visibility="collapsed")
with fc2:
    status_filter = st.selectbox("Status", ["All", "Upcoming", "Past"], key="me_status",
                                  label_visibility="collapsed")
with fc3:
    if st.button("🔄 Refresh", use_container_width=True, type="secondary"):
        get_all_events.clear()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── LOAD EVENTS ───────────────────────────────────────────────────────────────
all_events = get_all_events()
today      = date.today()

# Apply filters
filtered = all_events
if search_q.strip():
    filtered = [e for e in filtered if search_q.lower() in str(e.get("title","")).lower()]
if status_filter == "Upcoming":
    filtered = [e for e in filtered if e.get("event_date") and e["event_date"] >= today]
elif status_filter == "Past":
    filtered = [e for e in filtered if e.get("event_date") and e["event_date"] < today]

# Count badge
st.markdown(f"""
<div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.75rem;">
    Showing <span style="color:var(--accent);font-weight:600;">{len(filtered)}</span>
    of {len(all_events)} events
</div>
""", unsafe_allow_html=True)

if not filtered:
    empty_state("📭", "No events found. Create one first!")
    st.stop()

# ── EVENT CARDS WITH EXPANDERS ────────────────────────────────────────────────
for event in filtered:
    eid    = event["id"]
    title  = event.get("title", "Untitled")
    reg_ct = event.get("registration_count", 0)
    cap    = event.get("capacity", 0)

    with st.expander(f"{'📅' if event.get('event_date',today) >= today else '✅'}  {title}   ·   {reg_ct}/{cap} registered", expanded=False):
        tabs = st.tabs(["📋 Details", "✏️ Edit Event", "📝 Edit Fields", "🗑️ Delete"])

        # ── TAB 1: DETAILS ──────────────────────────────────────────────────
        with tabs[0]:
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"""
                **Title:** {title}
                **Date:** {event.get('event_date','—')}
                **Deadline:** {event.get('deadline','—')}
                **Capacity:** {cap}
                **Registered:** {reg_ct}
                """)
            with d2:
                desc = event.get("description","—")
                st.markdown(f"**Description:** {desc[:300] + '…' if len(str(desc)) > 300 else desc}")
                if event.get("image_url"):
                    st.image(event["image_url"], width=300)

            section_title("Event Info Fields")
            ef = get_event_fields(eid)
            if ef:
                for f in ef:
                    st.markdown(f"""
                    <div class="field-row">
                        <span style="color:var(--text-primary);font-size:0.85rem;">
                            <b>{f['field_name']}</b>
                        </span>
                        <span style="color:var(--accent);font-size:0.78rem;">
                            {f['field_type']}
                        </span>
                        <span style="color:var(--text-secondary);font-size:0.82rem;">
                            {f.get('field_value','') or '—'}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No custom event fields.")

            section_title("Registration Form Fields")
            rf = get_registration_fields(eid)
            if rf:
                for f in rf:
                    req_badge = "🔴 Required" if f.get("is_required") else "⚪ Optional"
                    st.markdown(f"""
                    <div class="field-row">
                        <span style="color:var(--text-primary);font-size:0.85rem;">
                            <b>{f['field_name']}</b>
                        </span>
                        <span style="color:var(--accent);font-size:0.78rem;">{f['field_type']}</span>
                        <span style="font-size:0.72rem;color:var(--text-muted);">{req_badge}</span>
                        {"" if not f.get('options') else f'<span style="font-size:0.72rem;color:var(--text-secondary);">Options: {f["options"]}</span>'}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No custom registration fields.")

        # ── TAB 2: EDIT EVENT ────────────────────────────────────────────────
        with tabs[1]:
            with st.form(f"edit_event_{eid}", clear_on_submit=False):
                ec1, ec2 = st.columns([2, 1])
                with ec1:
                    new_title = st.text_input("Title", value=title, key=f"et_{eid}")
                with ec2:
                    new_cap = st.number_input("Capacity", value=int(cap),
                                               min_value=int(reg_ct),
                                               key=f"ec_{eid}",
                                               help=f"Min: {reg_ct} (current registrations)")

                new_desc = st.text_area("Description",
                                        value=str(event.get("description","") or ""),
                                        height=100, key=f"ed_{eid}")
                ed1, ed2, ed3 = st.columns(3)
                with ed1:
                    raw_date = event.get("event_date")
                    if raw_date and not isinstance(raw_date, date):
                        raw_date = date.fromisoformat(str(raw_date))
                    new_date = st.date_input("Event Date", value=raw_date or today, key=f"edate_{eid}")
                with ed2:
                    raw_dl = event.get("deadline")
                    if raw_dl and not isinstance(raw_dl, date):
                        raw_dl = date.fromisoformat(str(raw_dl))
                    new_dl = st.date_input("Deadline", value=raw_dl or today, key=f"edl_{eid}")
                with ed3:
                    new_img = st.text_input("Image URL",
                                             value=str(event.get("image_url","") or ""),
                                             key=f"eimg_{eid}")

                if st.form_submit_button("💾 Save Changes", use_container_width=False):
                    errs = []
                    if not new_title.strip():
                        errs.append("Title cannot be empty.")
                    if new_dl and new_dl > new_date:
                        errs.append("Deadline must be before event date.")
                    if errs:
                        for e in errs:
                            st.error(e)
                    else:
                        with st.spinner("Saving…"):
                            update_event(
                                eid,
                                title=new_title.strip(),
                                description=new_desc.strip(),
                                event_date=str(new_date),
                                image_url=new_img.strip() or None,
                                capacity=new_cap,
                                deadline=str(new_dl) if new_dl else None,
                            )
                        st.success("✅ Event updated!")
                        get_all_events.clear()
                        st.rerun()

        # ── TAB 3: EDIT FIELDS ───────────────────────────────────────────────
        with tabs[2]:
            st.caption("Add or remove fields. Changes save immediately.")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                render_event_field_builder(event_id=eid, key_prefix=f"ef_{eid}")
            with f_col2:
                render_registration_field_builder(event_id=eid, key_prefix=f"rf_{eid}")

        # ── TAB 4: DELETE ────────────────────────────────────────────────────
        with tabs[3]:
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);
                        border-radius:var(--radius-md);padding:1.5rem;margin-bottom:1rem;">
                <div style="color:#ef4444;font-weight:600;margin-bottom:0.5rem;">
                    ⚠️ Danger Zone
                </div>
                <div style="color:var(--text-secondary);font-size:0.85rem;">
                    Deleting <b>{title}</b> will permanently remove the event and all
                    <b>{reg_ct} registrations</b>. This cannot be undone.
                </div>
            </div>
            """, unsafe_allow_html=True)

            confirm_key = f"confirm_del_{eid}"
            st.checkbox(f"I confirm I want to delete '{title}'", key=confirm_key)

            if st.button("🗑️ Delete Event", key=f"del_btn_{eid}",
                          type="secondary", use_container_width=False):
                if st.session_state.get(confirm_key):
                    with st.spinner("Deleting…"):
                        delete_event(eid)
                    st.success(f"Event '{title}' deleted.")
                    get_all_events.clear()
                    st.rerun()
                else:
                    st.warning("Please check the confirmation box first.")
