# utils/db.py
# MySQL connection with pooling — production-ready

import mysql.connector
from mysql.connector import pooling, Error
import streamlit as st
import os
from contextlib import contextmanager
from dotenv import load_dotenv
load_dotenv()

# ── CONFIG ──────────────────────────────────────────────────────────────────
# DB_CONFIG = {
#     "host":     os.getenv("DB_HOST",     "localhost"),
#     "port":     int(os.getenv("DB_PORT", "3306")),
#     "user":     os.getenv("DB_USER",     "root"),
#     "password": os.getenv("DB_PASSWORD", ""),
#     "database": os.getenv("DB_NAME",     "campus_events"),
#     "charset":  "utf8mb4",
#     "autocommit": False,
#     "connection_timeout": 10,
#     "use_pure": True,
# }

DB_CONFIG = {
    "host": st.secrets["DB_HOST"],
    "port": int(st.secrets["DB_PORT"]),
    "user": st.secrets["DB_USER"],
    "password": st.secrets["DB_PASSWORD"],
    "database": st.secrets["DB_NAME"],
    "connection_timeout": 10,
}

POOL_CONFIG = {
    **DB_CONFIG,
    "pool_name":    "campus_pool",
    "pool_size":    5,
    "pool_reset_session": True,
}

# ── POOL SINGLETON ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_pool():
    try:
        pool = mysql.connector.pooling.MySQLConnectionPool(**POOL_CONFIG)
        return pool
    except Error as e:
        # Don't call st.error here — cache_resource runs outside page context
        # Caller will handle the None return
        print(f"[DB] Pool creation failed: {e}")
        @st.cache_resource(show_spinner=False)
        def get_pool():
            pool = mysql.connector.pooling.MySQLConnectionPool(**POOL_CONFIG)
            return pool


# ── CONTEXT MANAGER ──────────────────────────────────────────────────────────
@contextmanager
def get_connection():
    """Get a connection from pool, auto-commit or rollback, always release."""
    pool = get_pool()

    # Guard: pool is None means DB credentials are wrong or DB is unreachable
    if pool is None:
        raise ConnectionError(
            "Cannot connect to MySQL. "
            "Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME in your .env file."
        )

    conn = None
    try:
        conn = pool.get_connection()
        yield conn
        conn.commit()
    except Error as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        raise e
    finally:
        if conn:
            try:
                if conn.is_connected():
                    conn.close()
            except Exception:
                pass


# ── QUERY HELPERS ─────────────────────────────────────────────────────────────
def execute_query(sql: str, params: tuple = None, fetch: str = None):
    """
    fetch = None     → execute only (INSERT/UPDATE/DELETE)
    fetch = 'one'    → fetchone()
    fetch = 'all'    → fetchall()
    Returns: lastrowid for INSERT, rows for SELECT, rowcount for DML
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        if fetch == "all":
            return cursor.fetchall()
        if fetch == "one":
            return cursor.fetchone()
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount


def execute_many(sql: str, params_list: list):
    """Bulk insert/update."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        return cursor.rowcount


# ── INIT DATABASE (run once) ──────────────────────────────────────────────────
def init_db():
    """Create all tables if they don't exist."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS admins (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            username      VARCHAR(80)  NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS events (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            title       VARCHAR(200) NOT NULL,
            description TEXT,
            event_date  DATE         NOT NULL,
            image_url   TEXT,
            capacity    INT          NOT NULL DEFAULT 100,
            deadline    DATE,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS event_fields (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            event_id    INT          NOT NULL,
            field_name  VARCHAR(100) NOT NULL,
            field_type  ENUM('text','number','date','dropdown') NOT NULL DEFAULT 'text',
            field_value TEXT,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS registration_fields (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            event_id    INT          NOT NULL,
            field_name  VARCHAR(100) NOT NULL,
            field_type  ENUM('text','number','date','dropdown') NOT NULL DEFAULT 'text',
            is_required TINYINT(1) DEFAULT 1,
            options     TEXT,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            event_id   INT         NOT NULL,
            name       VARCHAR(150) NOT NULL,
            prn        VARCHAR(50)  NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_prn_event (prn, event_id),
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS registration_answers (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            registration_id INT  NOT NULL,
            field_id        INT  NOT NULL,
            value           TEXT,
            FOREIGN KEY (registration_id) REFERENCES registrations(id) ON DELETE CASCADE,
            FOREIGN KEY (field_id)        REFERENCES registration_fields(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    ]
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for stmt in statements:
                cursor.execute(stmt)
        return True
    except Error as e:
        st.error(f"DB init error: {e}")
        return False


def test_connection() -> bool:
    try:
        if get_pool() is None:
            return False
        result = execute_query("SELECT 1 AS ok", fetch="one")
        return result and result.get("ok") == 1
    except Exception:
        return False