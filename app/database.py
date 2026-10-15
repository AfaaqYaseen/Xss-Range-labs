import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "range.db")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stored_values (
            lab_id TEXT NOT NULL,
            field TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (lab_id, field)
        )
    """)
    conn.commit()
    conn.close()


def set_stored(lab_id: str, field: str, value: str):
    conn = _conn()
    conn.execute(
        "INSERT INTO stored_values (lab_id, field, value) VALUES (?, ?, ?) "
        "ON CONFLICT(lab_id, field) DO UPDATE SET value=excluded.value",
        (lab_id, field, value),
    )
    conn.commit()
    conn.close()


def get_stored(lab_id: str, field: str) -> str:
    conn = _conn()
    row = conn.execute(
        "SELECT value FROM stored_values WHERE lab_id=? AND field=?", (lab_id, field)
    ).fetchone()
    conn.close()
    return row["value"] if row else ""


def get_all_stored(lab_id: str) -> dict:
    conn = _conn()
    rows = conn.execute("SELECT field, value FROM stored_values WHERE lab_id=?", (lab_id,)).fetchall()
    conn.close()
    return {r["field"]: r["value"] for r in rows}


def reset_stored(lab_id: str):
    conn = _conn()
    conn.execute("DELETE FROM stored_values WHERE lab_id=?", (lab_id,))
    conn.commit()
    conn.close()
