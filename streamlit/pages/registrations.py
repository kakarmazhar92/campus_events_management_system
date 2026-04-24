# pages/registrations.py

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from datetime import date

from utils.auth    import require_auth
from utils.helpers import load_css
from utils.queries import (
    get_all_events, get_registrations, get_registration_answers,
    delete_registration, get_export_df,
)
from components.sidebar import render_sidebar
from components.navbar  import render_navbar
from components.cards   import page_header, section_title, empty_state
from components.forms   import csv_download_button

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
import streamlit as st

st.set_page_config(
    page_title="Campus Events Admin",
    layout="wide",
    initial_sidebar_state="expanded"   # 🔥 important
)

load_css()

require_auth()
render_sidebar(active_page="Registrations")
render_navbar("Registrations")

page_header("Student", "Registrations", "View, search, filter and export all registrations")

# ── FILTERS ───────────────────────────────────────────────────────────────────
all_events = get_all_events()
event_map  = {e["title"]: e["id"] for e in all_events}

fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
with fc1:
    selected_event = st.selectbox(
        "Filter by Event", ["All Events"] + list(event_map.keys()),
        key="reg_event_filter", label_visibility="collapsed"
    )
with fc2:
    prn_search = st.text_input("Search PRN", placeholder="Search by PRN…",
                                key="reg_prn", label_visibility="collapsed")
with fc3:
    name_search = st.text_input("Search Name", placeholder="Search by name…",
                                 key="reg_name", label_visibility="collapsed")
with fc4:
    if st.button("🔄", help="Refresh", use_container_width=True, type="secondary"):
        get_registrations.clear()
        st.rerun()

selected_event_id = event_map.get(selected_event) if selected_event != "All Events" else None

# ── LOAD REGISTRATIONS ────────────────────────────────────────────────────────
with st.spinner("Loading registrations…"):
    rows = get_registrations(selected_event_id)

df = pd.DataFrame(rows) if rows else pd.DataFrame()

# Apply client-side filters
if not df.empty:
    if prn_search.strip():
        df = df[df["prn"].str.contains(prn_search.strip(), case=False, na=False)]
    if name_search.strip():
        df = df[df["name"].str.contains(name_search.strip(), case=False, na=False)]

# ── STATS ROW ──────────────────────────────────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)
with s1:
    total_regs = len(rows) if rows else 0
    st.markdown(f"""
    <div class="kpi-card" style="padding:1rem;">
        <div class="kpi-label">Total Registrations</div>
        <div class="kpi-value" style="font-size:1.6rem;">{total_regs}</div>
    </div>""", unsafe_allow_html=True)
with s2:
    filtered_count = len(df) if not df.empty else 0
    st.markdown(f"""
    <div class="kpi-card" style="padding:1rem;">
        <div class="kpi-label">Filtered Results</div>
        <div class="kpi-value" style="font-size:1.6rem;">{filtered_count}</div>
    </div>""", unsafe_allow_html=True)
with s3:
    unique_students = df["prn"].nunique() if not df.empty and "prn" in df.columns else 0
    st.markdown(f"""
    <div class="kpi-card" style="padding:1rem;">
        <div class="kpi-label">Unique Students</div>
        <div class="kpi-value" style="font-size:1.6rem;">{unique_students}</div>
    </div>""", unsafe_allow_html=True)
with s4:
    today_count = 0
    if not df.empty and "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
        today_count = int((df["created_at"].dt.date == date.today()).sum())
    st.markdown(f"""
    <div class="kpi-card" style="padding:1rem;">
        <div class="kpi-label">Today's Sign-ups</div>
        <div class="kpi-value" style="font-size:1.6rem;">{today_count}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── MAIN TABLE + EXPORT ───────────────────────────────────────────────────────
t_col, e_col = st.columns([5, 1])

with t_col:
    section_title(f"Registration List {'— ' + selected_event if selected_event != 'All Events' else ''}")

    if df.empty:
        empty_state("👥", "No registrations found for the selected filters.")
    else:
        # Display columns
        display_cols = [c for c in ["name","prn","event_title","event_date","created_at"] if c in df.columns]
        display_df = df[display_cols].copy()

        col_config = {
            "name":        st.column_config.TextColumn("Student Name", width="medium"),
            "prn":         st.column_config.TextColumn("PRN", width="small"),
            "event_title": st.column_config.TextColumn("Event", width="large"),
            "event_date":  st.column_config.DateColumn("Event Date", format="MMM DD, YYYY"),
            "created_at":  st.column_config.DatetimeColumn("Registered At", format="MMM DD, YYYY HH:mm"),
        }

        selection = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=col_config,
            on_select="rerun",
            selection_mode="single-row",
        )

        # Row detail popup
        sel_rows = selection.selection.get("rows", [])
        if sel_rows:
            sel_row = df.iloc[sel_rows[0]]
            reg_id  = int(sel_row.get("id", 0))

            with st.expander(f"📋 Details — {sel_row.get('name','?')} ({sel_row.get('prn','?')})", expanded=True):
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown(f"""
                    **Name:** {sel_row.get('name','—')}
                    **PRN:** {sel_row.get('prn','—')}
                    **Event:** {sel_row.get('event_title','—')}
                    **Registered:** {sel_row.get('created_at','—')}
                    """)
                with dc2:
                    answers = get_registration_answers(reg_id)
                    if answers:
                        section_title("Form Answers")
                        for ans in answers:
                            st.markdown(f"""
                            <div class="field-row">
                                <span style="color:var(--text-secondary);font-size:0.82rem;">
                                    {ans['field_name']}
                                </span>
                                <span style="color:var(--text-primary);font-size:0.85rem;font-weight:500;">
                                    {ans.get('value','—') or '—'}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("No additional form answers.")

                st.markdown("<br>", unsafe_allow_html=True)
                del_confirm_key = f"del_reg_confirm_{reg_id}"
                st.checkbox("Confirm delete this registration", key=del_confirm_key)
                if st.button("🗑️ Delete Registration", key=f"del_reg_{reg_id}",
                              type="secondary"):
                    if st.session_state.get(del_confirm_key):
                        delete_registration(reg_id)
                        st.success("Registration deleted.")
                        st.rerun()
                    else:
                        st.warning("Check the confirmation box first.")

with e_col:
    section_title("Export")
    st.markdown("<br>", unsafe_allow_html=True)

    # Full export (selected event or all)
    export_df = get_export_df(selected_event_id)
    fname = f"registrations_{selected_event.replace(' ','_')}_{date.today()}.csv" \
        if selected_event != "All Events" else f"all_registrations_{date.today()}.csv"
    csv_download_button(export_df, filename=fname, label="⬇️ Export All")

    # Filtered export
    st.markdown("<br>", unsafe_allow_html=True)
    if not df.empty:
        filtered_csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export Filtered",
            data=filtered_csv,
            file_name=f"filtered_{date.today()}.csv",
            mime="text/csv",
        )
        st.caption(f"{len(df)} rows")

    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Quick Stats")
    if not df.empty and "event_title" in df.columns:
        event_counts = df["event_title"].value_counts()
        for ev, cnt in event_counts.head(5).items():
            pct = int(cnt / len(df) * 100)
            short = str(ev)[:18] + "…" if len(str(ev)) > 18 else str(ev)
            st.markdown(f"""
            <div style="margin-bottom:0.5rem;">
                <div style="display:flex;justify-content:space-between;
                            font-size:0.72rem;color:var(--text-muted);margin-bottom:3px;">
                    <span>{short}</span><span>{cnt}</span>
                </div>
                <div style="background:var(--bg-secondary);border-radius:3px;height:4px;">
                    <div style="width:{pct}%;height:100%;background:var(--accent);border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)