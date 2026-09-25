import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("TTJ_DB_PATH", os.path.join(os.path.dirname(__file__), "../../database/ttj.db"))

def get_db_connection():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "../../database/schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with get_db() as conn:
        conn.executescript(schema_sql)
    print("Database initialized successfully at:", DB_PATH)

def dict_from_row(row):
    if row is None:
        return None
    return dict(row)

def dicts_from_rows(rows):
    return [dict(r) for r in rows]
