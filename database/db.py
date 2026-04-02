# -*- coding: utf-8 -*-
"""Инициализация и подключение к БД."""

import sqlite3

from config import DATABASE_PATH


def get_db_conn() -> sqlite3.Connection:
    """Возвращает соединение с SQLite базой данных."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Создаёт таблицы, если они ещё не существуют."""
    with get_db_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                device_type TEXT NOT NULL,
                description TEXT NOT NULL,
                preferred_time TEXT NOT NULL,
                telegram_user_id INTEGER,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                telegram_user_id INTEGER,
                telegram_username TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                answer_text TEXT,
                created_at TEXT NOT NULL,
                answered_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_repairs_order_number ON repairs(order_number)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status)")
