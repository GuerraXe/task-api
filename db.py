from collections.abc import Generator
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).with_name("tasks.db")


def init_db() -> None:
    """Create the local tasks table without replacing existing data."""
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=5.0,
        check_same_thread=False,
    )
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                hours REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield one dictionary-row connection and always close it afterward."""
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=5.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
