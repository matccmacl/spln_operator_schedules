import sqlite3
from contextlib import contextmanager
from src.config import DB_PATH

@contextmanager
def get_connection():
    """
    Context manager for SQLite connections.
    Enables WAL mode for high concurrency in Streamlit,
    enforces foreign key constraints, wraps in a transaction,
    and guarantees connection closure.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    try:
        # Performance & Concurrency optimization
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
