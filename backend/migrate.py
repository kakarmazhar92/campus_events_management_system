# backend/migrate.py
# Run ONCE: python migrate.py
# Patches the existing DB (created by Streamlit) to work with FastAPI

import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "campus_events"),
)
cursor = conn.cursor()

migrations = [
    # 1. Create users table (student accounts — new, doesn't exist yet)
    """
    CREATE TABLE IF NOT EXISTS users (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        name          VARCHAR(150) NOT NULL,
        email         VARCHAR(200) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 2. Add user_id to registrations (nullable — old rows have no user)
    """
    ALTER TABLE registrations
        ADD COLUMN IF NOT EXISTS user_id INT NULL DEFAULT NULL
        AFTER event_id;
    """,

    # 3. Add FK for user_id (safe — nullable)
    # (skip if already exists — wrapped below)

    # 4. Make sure event_fields.field_value allows NULL
    """
    ALTER TABLE event_fields
        MODIFY COLUMN field_value TEXT NULL DEFAULT NULL;
    """,

    # 5. Make sure registration_fields.options allows NULL
    """
    ALTER TABLE registration_fields
        MODIFY COLUMN options TEXT NULL DEFAULT NULL;
    """,

    # 6. Make sure events.deadline allows NULL
    """
    ALTER TABLE events
        MODIFY COLUMN deadline DATE NULL DEFAULT NULL;
    """,

    # 7. Make sure events.image_url allows NULL
    """
    ALTER TABLE events
        MODIFY COLUMN image_url TEXT NULL DEFAULT NULL;
    """,
]

# FK must be added separately (might already exist)
fk_migration = """
    ALTER TABLE registrations
        ADD CONSTRAINT fk_reg_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL;
"""

print("🔄 Running migrations...")
for i, sql in enumerate(migrations, 1):
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"  ✅ Migration {i} OK")
    except mysql.connector.Error as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print(f"  ⏭  Migration {i} skipped (already applied)")
        else:
            print(f"  ⚠️  Migration {i} warning: {e}")

# FK separately
try:
    cursor.execute(fk_migration)
    conn.commit()
    print("  ✅ FK constraint added")
except mysql.connector.Error as e:
    print(f"  ⏭  FK skipped: {e}")

cursor.close()
conn.close()
print("\n✅ All migrations done. You can now run: uvicorn main:app --reload")