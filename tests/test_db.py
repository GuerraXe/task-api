import sqlite3

import pytest

import db


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    database_path = tmp_path / "tasks.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    return database_path


def test_init_db_creates_tasks_table(temporary_database) -> None:
    db.init_db()

    with sqlite3.connect(temporary_database) as connection:
        columns = connection.execute("PRAGMA table_info(tasks)").fetchall()

    assert [(column[1], column[2]) for column in columns] == [
        ("id", "INTEGER"),
        ("title", "TEXT"),
        ("hours", "REAL"),
    ]
    assert columns[0][5] == 1


def test_init_db_preserves_existing_rows(temporary_database) -> None:
    db.init_db()
    with sqlite3.connect(temporary_database) as connection:
        connection.execute(
            "INSERT INTO tasks (title, hours) VALUES (?, ?)",
            ("Algorithms", 2.0),
        )

    db.init_db()

    with sqlite3.connect(temporary_database) as connection:
        count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    assert count == 1


def test_get_db_uses_row_factory_and_closes_connection(
    temporary_database,
) -> None:
    db.init_db()
    dependency = db.get_db()
    connection = next(dependency)
    connection.execute(
        "INSERT INTO tasks (title, hours) VALUES (?, ?)",
        ("Algorithms", 2.0),
    )
    connection.commit()

    row = connection.execute("SELECT * FROM tasks").fetchone()
    assert row["title"] == "Algorithms"

    dependency.close()
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_get_db_rolls_back_and_closes_after_error(temporary_database) -> None:
    db.init_db()
    dependency = db.get_db()
    connection = next(dependency)
    connection.execute(
        "INSERT INTO tasks (title, hours) VALUES (?, ?)",
        ("Algorithms", 2.0),
    )

    with pytest.raises(RuntimeError, match="endpoint failed"):
        dependency.throw(RuntimeError("endpoint failed"))

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")

    with sqlite3.connect(temporary_database) as verification_connection:
        count = verification_connection.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]
    assert count == 0
