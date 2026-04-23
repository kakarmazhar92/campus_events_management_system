# utils/queries.py
# All DB queries in one place — clean separation of concerns

import streamlit as st
import pandas as pd
from datetime import date
from utils.db import execute_query, execute_many
from mysql.connector import IntegrityError


# ══════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════

@st.cache_data(ttl=30, show_spinner=False)
def get_all_events() -> list[dict]:
    return execute_query(
        """
        SELECT  e.*,
                COUNT(r.id) AS registration_count
        FROM    events e
        LEFT JOIN registrations r ON r.event_id = e.id
        GROUP BY e.id
        ORDER BY e.event_date DESC
        """,
        fetch="all",
    ) or []


def get_event_by_id(event_id: int) -> dict | None:
    return execute_query(
        "SELECT * FROM events WHERE id = %s", (event_id,), fetch="one"
    )


def create_event(
    title: str, description: str, event_date: date,
    image_url: str, capacity: int, deadline: date
) -> int:
    eid = execute_query(
        """
        INSERT INTO events (title, description, event_date, image_url, capacity, deadline)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (title, description, str(event_date), image_url or None, capacity, str(deadline) if deadline else None),
    )
    get_all_events.clear()
    return eid


def update_event(event_id: int, **kwargs) -> bool:
    allowed = {"title", "description", "event_date", "image_url", "capacity", "deadline"}
    fields  = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    execute_query(
        f"UPDATE events SET {set_clause} WHERE id = %s",
        (*fields.values(), event_id),
    )
    get_all_events.clear()
    return True


def delete_event(event_id: int) -> bool:
    execute_query("DELETE FROM events WHERE id = %s", (event_id,))
    get_all_events.clear()
    return True


# ══════════════════════════════════════════════════════════
#  EVENT FIELDS (custom display fields)
# ══════════════════════════════════════════════════════════

def get_event_fields(event_id: int) -> list[dict]:
    return execute_query(
        "SELECT * FROM event_fields WHERE event_id = %s ORDER BY id",
        (event_id,), fetch="all"
    ) or []


def add_event_field(event_id: int, field_name: str, field_type: str, field_value: str = "") -> int:
    return execute_query(
        "INSERT INTO event_fields (event_id, field_name, field_type, field_value) VALUES (%s,%s,%s,%s)",
        (event_id, field_name, field_type, field_value),
    )


def delete_event_field(field_id: int):
    execute_query("DELETE FROM event_fields WHERE id = %s", (field_id,))


# ══════════════════════════════════════════════════════════
#  REGISTRATION FIELDS (form fields)
# ══════════════════════════════════════════════════════════

def get_registration_fields(event_id: int) -> list[dict]:
    return execute_query(
        "SELECT * FROM registration_fields WHERE event_id = %s ORDER BY id",
        (event_id,), fetch="all"
    ) or []


def add_registration_field(
    event_id: int, field_name: str, field_type: str,
    is_required: bool = True, options: str = ""
) -> int:
    return execute_query(
        """
        INSERT INTO registration_fields
            (event_id, field_name, field_type, is_required, options)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (event_id, field_name, field_type, int(is_required), options),
    )


def delete_registration_field(field_id: int):
    execute_query("DELETE FROM registration_fields WHERE id = %s", (field_id,))


# ══════════════════════════════════════════════════════════
#  REGISTRATIONS
# ══════════════════════════════════════════════════════════

@st.cache_data(ttl=15, show_spinner=False)
def get_registrations(event_id: int | None = None) -> list[dict]:
    if event_id:
        return execute_query(
            """
            SELECT r.id, r.name, r.prn, f.field_name, a.value, r.created_at,
                   e.title AS event_title, e.event_date
            FROM   registrations r
            INNER JOIN   events e ON e.id = r.event_id
            INNER JOIN registration_answers a
            ON r.id = a.registration_id
            INNER JOIN registration_fields f
            ON a.field_id = f.id
            WHERE  r.event_id = %s
            ORDER  BY r.created_at DESC
            """,
            (event_id,), fetch="all"
        ) or []
    return execute_query(
        """
        SELECT r.id, r.name, r.prn, r.created_at,
               e.title AS event_title, e.event_date
        FROM   registrations r
        JOIN   events e ON e.id = r.event_id
        ORDER  BY r.created_at DESC
        """,
        fetch="all"
    ) or []


def get_registration_answers(registration_id: int) -> list[dict]:
    return execute_query(
        """
        SELECT rf.field_name, ra.value
        FROM   registration_answers ra
        JOIN   registration_fields rf ON rf.id = ra.field_id
        WHERE  ra.registration_id = %s
        """,
        (registration_id,), fetch="all"
    ) or []


def register_student(
    event_id: int, name: str, prn: str, answers: dict[int, str]
) -> tuple[bool, str]:
    """Atomic registration with capacity check."""
    try:
        # Check capacity atomically
        cap_row = execute_query(
            """
            SELECT e.capacity,
                   COUNT(r.id) AS reg_count
            FROM   events e
            LEFT JOIN registrations r ON r.event_id = e.id
            WHERE  e.id = %s
            GROUP  BY e.id
            """,
            (event_id,), fetch="one"
        )
        if not cap_row:
            return False, "Event not found."
        if cap_row["reg_count"] >= cap_row["capacity"]:
            return False, "Event is full. Registration closed."

        reg_id = execute_query(
            "INSERT INTO registrations (event_id, name, prn) VALUES (%s, %s, %s)",
            (event_id, name, prn),
        )
        if answers:
            execute_many(
                "INSERT INTO registration_answers (registration_id, field_id, value) VALUES (%s,%s,%s)",
                [(reg_id, fid, val) for fid, val in answers.items()],
            )
        get_registrations.clear()
        return True, "Registered successfully."
    except IntegrityError:
        return False, "This PRN is already registered for this event."
    except Exception as e:
        return False, str(e)


def delete_registration(reg_id: int):
    execute_query("DELETE FROM registrations WHERE id = %s", (reg_id,))
    get_registrations.clear()


# ══════════════════════════════════════════════════════════
#  ANALYTICS
# ══════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def get_analytics_overview() -> dict:
    total_events = execute_query("SELECT COUNT(*) AS n FROM events", fetch="one")["n"]
    total_regs   = execute_query("SELECT COUNT(*) AS n FROM registrations", fetch="one")["n"]
    upcoming     = execute_query(
        "SELECT COUNT(*) AS n FROM events WHERE event_date >= CURDATE()", fetch="one"
    )["n"]
    today_regs   = execute_query(
        "SELECT COUNT(*) AS n FROM registrations WHERE DATE(created_at) = CURDATE()",
        fetch="one"
    )["n"]
    return {
        "total_events":  total_events,
        "total_regs":    total_regs,
        "upcoming":      upcoming,
        "today_regs":    today_regs,
    }


@st.cache_data(ttl=60, show_spinner=False)
def get_registrations_per_event() -> pd.DataFrame:
    rows = execute_query(
        """
        SELECT  e.title,
                e.capacity,
                COUNT(r.id)  AS registrations,
                ROUND(COUNT(r.id) / e.capacity * 100, 1) AS fill_pct
        FROM    events e
        LEFT JOIN registrations r ON r.event_id = e.id
        GROUP BY e.id
        ORDER BY registrations DESC
        LIMIT 15
        """,
        fetch="all"
    ) or []
    return pd.DataFrame(rows)


@st.cache_data(ttl=60, show_spinner=False)
def get_registration_trend(days: int = 30) -> pd.DataFrame:
    rows = execute_query(
        f"""
        SELECT  DATE(created_at) AS reg_date,
                COUNT(*)         AS count
        FROM    registrations
        WHERE   created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        GROUP BY DATE(created_at)
        ORDER BY reg_date
        """,
        (days,), fetch="all"
    ) or []
    return pd.DataFrame(rows)


@st.cache_data(ttl=60, show_spinner=False)
def get_recent_registrations(limit: int = 10) -> pd.DataFrame:
    rows = execute_query(
        f"""
        SELECT  r.name, r.prn, e.title AS event,
                r.created_at AS registered_at
        FROM    registrations r
        JOIN    events e ON e.id = r.event_id
        ORDER   BY r.created_at DESC
        LIMIT   %s
        """,
        (limit,), fetch="all"
    ) or []
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════
#  EXPORT
# ══════════════════════════════════════════════════════════

def get_export_df(event_id: int | None = None) -> pd.DataFrame:
    rows = get_registrations(event_id)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    return df
