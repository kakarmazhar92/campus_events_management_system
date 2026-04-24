# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))        # BUG FIX: was crashing if env var missing
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = quote_plus(os.getenv("DB_PASSWORD", "")) # encode special chars in password
DB_NAME = os.getenv("DB_NAME", "campus_events")

DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# BUG FIX: was creating engine TWICE — first bare, then with pool config (duplicate, wasted conn)
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,   # auto-reconnect if DB drops connection
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()