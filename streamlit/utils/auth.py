# utils/auth.py
# Admin authentication — bcrypt hashing, session management

import hashlib
import secrets
import streamlit as st
from utils.db import execute_query
from mysql.connector import Error


# ── PASSWORD HASHING (SHA-256 + salt, bcrypt-like simplicity) ─────────────
def hash_password(password: str) -> str:
    """Hash password with SHA-256 + salt. For production use bcrypt."""
    salt = "campus_admin_salt_2024"          # Fixed salt for simplicity
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ── SEED DEFAULT ADMIN ────────────────────────────────────────────────────────
def seed_default_admin():
    """Insert default admin if none exists."""
    try:
        existing = execute_query(
            "SELECT id FROM admins LIMIT 1", fetch="one"
        )
        if not existing:
            execute_query(
                "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
                ("admin", hash_password("admin123")),
            )
    except Error:
        pass                       # Table might not exist yet — init_db handles it


# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login(username: str, password: str) -> bool:
    try:
        row = execute_query(
            "SELECT id, username, password_hash FROM admins WHERE username = %s",
            (username,),
            fetch="one",
        )
        if row and verify_password(password, row["password_hash"]):
            st.session_state["authenticated"] = True
            st.session_state["admin_id"]       = row["id"]
            st.session_state["admin_user"]     = row["username"]
            return True
        return False
    except Exception:
        return False


# ── LOGOUT ────────────────────────────────────────────────────────────────────
def logout():
    for key in ["authenticated", "admin_id", "admin_user"]:
        st.session_state.pop(key, None)


# ── GUARD ─────────────────────────────────────────────────────────────────────
def require_auth():
    """Call at top of every page. Redirects to login if not authenticated."""
    if not st.session_state.get("authenticated"):
        st.switch_page("pages/login.py")


# ── CHANGE PASSWORD ────────────────────────────────────────────────────────────
def change_password(admin_id: int, old_pass: str, new_pass: str) -> tuple[bool, str]:
    row = execute_query(
        "SELECT password_hash FROM admins WHERE id = %s",
        (admin_id,),
        fetch="one",
    )
    if not row:
        return False, "Admin not found."
    if not verify_password(old_pass, row["password_hash"]):
        return False, "Current password is incorrect."
    execute_query(
        "UPDATE admins SET password_hash = %s WHERE id = %s",
        (hash_password(new_pass), admin_id),
    )
    return True, "Password updated successfully."
