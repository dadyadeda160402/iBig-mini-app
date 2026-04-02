# -*- coding: utf-8 -*-
"""Модели данных и вспомогательные функции для работы с БД."""

import secrets
import sqlite3
import string
from datetime import datetime, timezone
from typing import Any, Optional

from database.db import get_db_conn


def utc_now_iso() -> str:
    """Возвращает текущее UTC-время в формате ISO 8601."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def generate_order_number() -> str:
    """Генерирует уникальный номер заказа вида iBig-YYYYMMDD-XXXXXX."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand = secrets.token_hex(3).upper()
    return f"iBig-{date_part}-{rand}"


def sanitize_text(x: Any, max_len: int = 3000) -> str:
    """Очищает и обрезает текстовое значение."""
    if x is None:
        return ""
    s = str(x).strip()
    if len(s) > max_len:
        s = s[:max_len]
    return s


def sanitize_phone(x: Any, max_len: int = 50) -> str:
    """Очищает номер телефона, оставляя только цифры, плюс и пробел."""
    s = sanitize_text(x, max_len=max_len)
    allowed = set(string.digits) | {"+", " "}
    return "".join(ch for ch in s if ch in allowed).strip()


def create_repair(
    name: str,
    phone: str,
    device_type: str,
    description: str,
    preferred_time: str,
    telegram_user_id: Optional[int],
) -> Optional[sqlite3.Row]:
    """Создаёт заявку на ремонт. Возвращает строку из БД или None при неудаче."""
    for _ in range(5):
        order_number = generate_order_number()
        try:
            with get_db_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO repairs
                    (order_number, name, phone, device_type, description, preferred_time, telegram_user_id, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?)
                    """,
                    (order_number, name, phone, device_type, description, preferred_time, telegram_user_id, utc_now_iso()),
                )
                conn.commit()
                return conn.execute("SELECT * FROM repairs WHERE order_number = ?", (order_number,)).fetchone()
        except sqlite3.IntegrityError:
            continue
    return None


def get_repair_by_order_number(order_number: str) -> Optional[sqlite3.Row]:
    """Возвращает заявку по номеру заказа."""
    with get_db_conn() as conn:
        return conn.execute(
            "SELECT order_number, status FROM repairs WHERE order_number = ?",
            (order_number,),
        ).fetchone()


def update_repair_status(order_number: str, status: str) -> bool:
    """Обновляет статус заявки. Возвращает True, если заявка найдена."""
    with get_db_conn() as conn:
        row = conn.execute("SELECT id FROM repairs WHERE order_number = ?", (order_number,)).fetchone()
        if not row:
            return False
        conn.execute("UPDATE repairs SET status = ? WHERE order_number = ?", (status, order_number))
        conn.commit()
        return True


def create_question(
    question_text: str,
    telegram_user_id: Optional[int],
    telegram_username: Optional[str],
) -> int:
    """Создаёт вопрос в БД. Возвращает ID вопроса."""
    with get_db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO questions (question_text, telegram_user_id, telegram_username, status, created_at)
            VALUES (?, ?, ?, 'new', ?)
            """,
            (question_text, telegram_user_id, telegram_username, utc_now_iso()),
        )
        question_id = int(cur.lastrowid)
        conn.commit()
        return question_id


def answer_question(question_id: int, answer_text: str) -> Optional[sqlite3.Row]:
    """Сохраняет ответ на вопрос. Возвращает строку вопроса или None."""
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM questions WHERE id = ? AND status = 'new'", (question_id,)).fetchone()
        if not row:
            return None
        conn.execute(
            """
            UPDATE questions
            SET status = 'answered', answer_text = ?, answered_at = ?
            WHERE id = ?
            """,
            (answer_text, utc_now_iso(), question_id),
        )
        conn.commit()
        return row
