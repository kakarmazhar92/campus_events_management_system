# pages/dashboard.py

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

from utils.auth    import require_auth
from utils.queries import (
    get_analytics_overview, get_registrations_per_event,
    get_registration_trend, get_recent_registrations,
    get_all_events, get_registrations,
)
from components.sidebar import render_sidebar
from components.navbar  import render_navbar
from components.cards   import kpi_card, page_header, section_title, empty_state
from components.forms   import csv_download_button

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CampusEvents Admin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
css_path = os.path.join(BASE_DIR, "assets", "styles.css")

if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("CSS file not found")

require_auth()
render_sidebar(active_page="Dashboard")
render_navbar("Dashboard")

# ── PLOTLY THEME ──────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk", color="#a0a0a0", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="#2a2a2a", zerolinecolor="#2a2a2a"),
    yaxis=dict(gridcolor="#2a2a2a", zerolinecolor="#2a2a2a"),
)

# ── HEADER ────────────────────────────────────────────────────────────────────
page_header("Analytics", "Dashboard", f"Last updated: {date.today().strftime('%B %d, %Y')}")

# ── FILTERS ──────────────────────────────────────────────────────────────────
with st.expander("🔍 Filters", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    all_events = get_all_events()
    event_options = {e["title"]: e["id"] for e in all_events}

    with fc1:
        selected_event_name = st.selectbox(
            "Filter by Event", ["All Events"] + list(event_options.keys()),
            key="dash_event_filter"
        )
    with fc2:
        trend_days = st.selectbox("Trend Period", [7, 14, 30, 60, 90], index=2,
                                  key="dash_trend_days")
    with fc3:
        recent_limit = st.selectbox("Recent Registrations", [5, 10, 20, 50], index=1,
                                    key="dash_recent_limit")

selected_event_id = event_options.get(selected_event_name) if selected_event_name != "All Events" else None

# ── KPI ROW ───────────────────────────────────────────────────────────────────
with st.spinner("Loading analytics…"):
    overview = get_analytics_overview()

k1, k2, k3, k4 = st.columns(4)
with k1: kpi_card("Total Events",       overview["total_events"],  "all time",         "📅")
with k2: kpi_card("Total Registrations",overview["total_regs"],    "all time",         "👥")
with k3: kpi_card("Upcoming Events",    overview["upcoming"],      "from today",       "🚀")
with k4: kpi_card("Today's Sign-ups",   overview["today_regs"],    "last 24 hours",    "⚡")

st.markdown("<br>", unsafe_allow_html=True)

# ── ROW 1: Bar + Trend ────────────────────────────────────────────────────────
col_bar, col_line = st.columns([3, 2])

with col_bar:
    section_title("Registrations Per Event")
    df_bar = get_registrations_per_event()
    if not df_bar.empty:
        fig_bar = px.bar(
            df_bar, x="registrations", y="title",
            orientation="h", color="fill_pct",
            color_continuous_scale=[[0,"#1e3a2f"],[0.5,"#f5b301"],[1,"#ef4444"]],
            labels={"registrations":"Registrations","title":"Event","fill_pct":"Fill %"},
            text="registrations",
        )
        fig_bar.update_traces(textposition="outside", textfont_size=10)
        fig_bar.update_coloraxes(showscale=False)
        fig_bar.update_layout(**PLOTLY_LAYOUT, height=380)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        empty_state("📊", "No event data yet.")

with col_line:
    section_title(f"Registration Trend ({trend_days}d)")
    df_trend = get_registration_trend(trend_days)
    if not df_trend.empty:
        fig_line = px.area(
            df_trend, x="reg_date", y="count",
            labels={"reg_date":"Date","count":"Registrations"},
            color_discrete_sequence=["#f5b301"],
        )
        fig_line.update_traces(
            fill="tozeroy",
            fillcolor="rgba(245,179,1,0.1)",
            line=dict(color="#f5b301", width=2),
        )
        fig_line.update_layout(**PLOTLY_LAYOUT, height=380)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        empty_state("📈", "No trend data yet.")

st.markdown("<br>", unsafe_allow_html=True)

# ── ROW 2: Capacity gauges ────────────────────────────────────────────────────
section_title("Event Capacity Fill Rate")
df_cap = get_registrations_per_event()
if not df_cap.empty:
    cols = st.columns(min(len(df_cap), 4))
    for i, (_, row) in enumerate(df_cap.head(4).iterrows()):
        with cols[i]:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=float(row.get("fill_pct", 0)),
                number={"suffix":"%","font":{"size":20,"color":"#f5b301","family":"JetBrains Mono"}},
                title={"text": row["title"][:20]+"…" if len(str(row["title"])) > 20 else row["title"],
                       "font":{"size":11,"color":"#a0a0a0"}},
                gauge={
                    "axis":{"range":[0,100],"tickcolor":"#2a2a2a","tickwidth":1},
                    "bar":{"color":"#f5b301","thickness":0.3},
                    "bgcolor":"#1e1e1e",
                    "bordercolor":"#2a2a2a",
                    "steps":[
                        {"range":[0,70],  "color":"#1a1a1a"},
                        {"range":[70,90], "color":"rgba(249,115,22,0.1)"},
                        {"range":[90,100],"color":"rgba(239,68,68,0.1)"},
                    ],
                    "threshold":{"line":{"color":"#ef4444","width":2},"thickness":0.8,"value":95},
                },
            ))
            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                height=200,
                margin=dict(l=10,r=10,t=30,b=10),
                font=dict(family="Space Grotesk"),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
else:
    empty_state("🎯", "No capacity data yet.")

st.markdown("<br>", unsafe_allow_html=True)

# ── RECENT REGISTRATIONS TABLE ────────────────────────────────────────────────
section_title("Recent Registrations")
c_table, c_export = st.columns([4, 1])

with c_table:
    df_recent = get_recent_registrations(recent_limit)
    if not df_recent.empty:
        st.dataframe(
            df_recent,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name":          st.column_config.TextColumn("Student Name"),
                "prn":           st.column_config.TextColumn("PRN"),
                "event":         st.column_config.TextColumn("Event"),
                "registered_at": st.column_config.DatetimeColumn("Registered At",
                                    format="MMM DD, YYYY HH:mm"),
            },
        )
    else:
        empty_state("👥", "No registrations yet.")

with c_export:
    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Export")
    df_export = get_recent_registrations(1000)
    if selected_event_id:
        rows = get_registrations(selected_event_id)
        df_export = pd.DataFrame(rows) if rows else pd.DataFrame()
    csv_download_button(
        df_export,
        filename=f"registrations_{date.today()}.csv",
        label="⬇️ Export CSV",
    )
    st.caption("Exports all visible registrations")

    if st.button("🔄 Refresh Data", use_container_width=True, type="secondary"):
        get_analytics_overview.clear()
        get_registrations_per_event.clear()
        get_registration_trend.clear()
        get_recent_registrations.clear()
        st.rerun()