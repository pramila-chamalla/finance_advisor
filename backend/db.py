import os
import sqlite3
from contextlib import closing
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DB_NAME = Path(
    os.getenv(
        "FINANCE_DB_PATH",
        str(Path(__file__).resolve().parent / "database" / "finance.db"),
    )
)


def get_connection() -> sqlite3.Connection:
    DB_NAME.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_NAME), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with closing(get_connection()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                salary REAL NOT NULL CHECK (salary >= 0),
                age INTEGER NOT NULL CHECK (age >= 18)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                description TEXT NOT NULL DEFAULT '',
                expense_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                goal_name TEXT NOT NULL,
                target_amount REAL NOT NULL CHECK (target_amount > 0),
                saved_amount REAL NOT NULL DEFAULT 0 CHECK (saved_amount >= 0)
            );

            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            """
        )

        _migrate_existing_database(connection)
        connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_expenses_user_date
                ON expenses(user_id, expense_date);
            CREATE INDEX IF NOT EXISTS idx_goals_user
                ON goals(user_id);
            CREATE INDEX IF NOT EXISTS idx_chats_user_created
                ON chats(user_id, created_at);
            """
        )
        connection.commit()


def _migrate_existing_database(connection: sqlite3.Connection) -> None:
    expense_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(expenses)")
    }
    if "expense_date" not in expense_columns:
        connection.execute("ALTER TABLE expenses ADD COLUMN expense_date TEXT")
        connection.execute(
            "UPDATE expenses SET expense_date = date('now') "
            "WHERE expense_date IS NULL"
        )

    chat_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(chats)")
    }
    if chat_columns and "created_at" not in chat_columns:
        connection.execute("ALTER TABLE chats ADD COLUMN created_at TEXT")
        connection.execute(
            "UPDATE chats SET created_at = datetime('now') WHERE created_at IS NULL"
        )
