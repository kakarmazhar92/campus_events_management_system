# components/cards.py

import streamlit as st
from datetime import date


def kpi_card(label: str, value, sub: str = "", icon: str = ""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"" if not sub else f'<div class="kpi-sub">{sub}</div>'}
    </div>
    """, unsafe_allow_html=True)


def event_status_badge(event_date: date | str) -> str:
    try:
        if isinstance(event_date, str):
            event_date = date.fromisoformat(str(event_date))
        today = date.today()
        if event_date > today:
            return '<span class="event-badge badge-upcoming">Upcoming</span>'
        if event_date == today:
            return '<span class="event-badge badge-active">Today</span>'
        return '<span class="event-badge badge-past">Past</span>'
    except Exception:
        return ""


def event_card(event: dict) -> None:
    reg_count = event.get("registration_count", 0)
    capacity  = event.get("capacity", 1)
    fill_pct  = round((reg_count / capacity) * 100) if capacity else 0
    badge     = event_status_badge(event.get("event_date"))

    bar_color = (
        "var(--success)"  if fill_pct < 70  else
        "var(--warning)"  if fill_pct < 90  else
        "var(--error)"
    )

    st.markdown(f"""
    <div class="event-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.6rem;">
            <div style="font-weight:600;font-size:1rem;color:var(--text-primary);">
                {event.get('title','Untitled')}
            </div>
            {badge}
        </div>
        <div style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:0.8rem;">
            📅 {event.get('event_date','—')} &nbsp;·&nbsp;
            🏛️ Capacity {capacity} &nbsp;·&nbsp;
            👥 {reg_count} registered
        </div>
        <div style="background:var(--bg-secondary);border-radius:4px;height:5px;overflow:hidden;">
            <div style="width:{fill_pct}%;height:100%;background:{bar_color};
                        border-radius:4px;transition:width 0.5s;"></div>
        </div>
        <div style="font-size:0.68rem;color:var(--text-muted);margin-top:4px;">
            {fill_pct}% full
        </div>
    </div>
    """, unsafe_allow_html=True)


def page_header(title: str, highlight: str = "", subtitle: str = ""):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{title} <span>{highlight}</span></div>
        {"" if not subtitle else f'<div class="page-subtitle">{subtitle}</div>'}
    </div>
    """, unsafe_allow_html=True)


def section_title(text: str):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def empty_state(icon: str = "📭", message: str = "No data found."):
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def form_section(title: str, icon: str = ""):
    st.markdown(f"""
    <div class="form-section-title">{icon} {title}</div>
    """, unsafe_allow_html=True)
