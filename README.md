# 🎓 CampusEvents — Admin Panel

A production-ready Streamlit admin dashboard for the Campus Event & Engagement Management System.

---

## 🗂️ Project Structure

```
campus_admin/
├── app.py                      ← Entry point (redirects to login)
├── .env.example                ← Copy to .env
├── requirements.txt
├── .streamlit/
│   └── config.toml             ← Dark theme config
│
├── pages/
│   ├── login.py                ← Admin login
│   ├── dashboard.py            ← Analytics dashboard
│   ├── create_event.py         ← Create events + dynamic fields
│   ├── manage_events.py        ← CRUD events
│   └── registrations.py        ← View, filter, export registrations
│
├── components/
│   ├── navbar.py               ← Top navbar
│   ├── sidebar.py              ← Navigation sidebar
│   ├── cards.py                ← KPI cards, event cards, helpers
│   └── forms.py                ← Dynamic field builders, CSV export
│
├── utils/
│   ├── db.py                   ← MySQL connection pool + query helpers
│   ├── auth.py                 ← Login, logout, password hashing
│   └── queries.py              ← All DB queries (cached with st.cache_data)
│
└── assets/
    └── styles.css              ← Full dark theme CSS
```

---

## ⚡ Quick Start

### 1. Clone and install
```bash
git clone <your-repo>
cd campus_admin
pip install -r requirements.txt
```

### 2. Configure database
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 3. Create MySQL database
```sql
CREATE DATABASE campus_events CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
> Tables are auto-created on first run by `init_db()`.

### 4. Run
```bash
streamlit run app.py
```
Open: http://localhost:8501

**Default credentials:** `admin / admin123`

---

## 🗄️ Database Schema

```sql
admins              → id, username, password_hash, created_at
events              → id, title, description, event_date, image_url, capacity, deadline, created_at
event_fields        → id, event_id, field_name, field_type, field_value
registration_fields → id, event_id, field_name, field_type, is_required, options
registrations       → id, event_id, name, prn, created_at  [UNIQUE: prn+event_id]
registration_answers→ id, registration_id, field_id, value
```

---

## 🚀 Deployment (Streamlit Cloud — Free)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select repo → Main file: `app.py`
4. Add Secrets (Settings → Secrets):
```toml
DB_HOST     = "your-neon-or-planetscale-host"
DB_PORT     = "3306"
DB_USER     = "your_user"
DB_PASSWORD = "your_password"
DB_NAME     = "campus_events"
```
5. Deploy → Get your public URL

> **Recommended DB for deployment:** [PlanetScale](https://planetscale.com) (free MySQL) or [Railway](https://railway.app)

---

## 🔐 Security

- Passwords hashed with SHA-256 + salt (upgrade to bcrypt for production)
- Session state auth guard on every page via `require_auth()`
- Admin panel URL separate from student frontend
- No student-facing routes in this app

---

## 🏗️ Architecture Notes

| Concern | Implementation |
|---|---|
| DB Connection Pooling | `MySQLConnectionPool` (pool_size=5) |
| Query Caching | `@st.cache_data(ttl=30–60s)` |
| Race Condition (capacity) | Atomic SQL `UPDATE … WHERE count < capacity` |
| Duplicate Registration | `UNIQUE(prn, event_id)` constraint + app-level check |
| Concurrency | Single admin — Streamlit session state is sufficient |
| Cache Invalidation | Manual `.clear()` after writes |

---

## 🎨 Theme

| Token | Value |
|---|---|
| Background | `#121212` |
| Card | `#1e1e1e` |
| Accent | `#f5b301` (yellow) |
| Text | `#f0f0f0` |
| Border | `#2a2a2a` |
| Success | `#22c55e` |
| Error | `#ef4444` |
