# -*- coding: utf-8 -*-
"""Модели данных и вспомогательные функции для работы с БД."""

import secrets
import sqlite3
import string
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, List

from database.db import get_db_conn


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def generate_order_number() -> str:
    """Генерирует короткий номер заказа вида iBig-NNNN."""
    num = secrets.randbelow(9000) + 1000
    return f"iBig-{num}"


def sanitize_text(x: Any, max_len: int = 3000) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    return s[:max_len] if len(s) > max_len else s


def sanitize_phone(x: Any, max_len: int = 50) -> str:
    s = sanitize_text(x, max_len=max_len)
    allowed = set(string.digits) | {"+", " ", "-"}
    return "".join(ch for ch in s if ch in allowed).strip()


# --- Repairs ---

def create_repair(
    name: str,
    phone: str,
    device_type: str,
    device_model: str,
    description: str,
    preferred_time: str,
    telegram_user_id: Optional[int],
    slot_id: Optional[int] = None,
) -> Optional[sqlite3.Row]:
    for _ in range(5):
        order_number = generate_order_number()
        try:
            with get_db_conn() as conn:
                cur = conn.execute(
                    """INSERT INTO repairs
                    (order_number, name, phone, device_type, device_model, description, preferred_time, telegram_user_id, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)""",
                    (order_number, name, phone, device_type, device_model, description, preferred_time, telegram_user_id, utc_now_iso()),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM repairs WHERE order_number = ?", (order_number,)).fetchone()
                if row and slot_id:
                    conn.execute(
                        "UPDATE time_slots SET is_booked = 1, repair_id = ? WHERE id = ? AND is_booked = 0",
                        (row["id"], slot_id),
                    )
                    conn.commit()
                return row
        except sqlite3.IntegrityError:
            continue
    return None


def get_repair_by_order_number(order_number: str) -> Optional[sqlite3.Row]:
    with get_db_conn() as conn:
        return conn.execute(
            "SELECT order_number, status FROM repairs WHERE order_number = ?",
            (order_number,),
        ).fetchone()


def update_repair_status(repair_id: int, status: str) -> bool:
    """Обновить статус заявки по ID (для админки)."""
    with get_db_conn() as conn:
        conn.execute("UPDATE repairs SET status = ? WHERE id = ?", (status, repair_id))
        conn.commit()
        return conn.total_changes > 0


def update_repair_status_by_order(order_number: str, status: str) -> bool:
    """Обновить статус заявки по номеру заказа."""
    with get_db_conn() as conn:
        conn.execute("UPDATE repairs SET status = ? WHERE order_number = ?", (status, order_number))
        conn.commit()
        return conn.total_changes > 0


def get_all_repairs(status_filter: Optional[str] = None) -> List[sqlite3.Row]:
    """Получить все заявки, опционально фильтруя по статусу."""
    with get_db_conn() as conn:
        if status_filter:
            return conn.execute(
                "SELECT * FROM repairs WHERE status = ? ORDER BY created_at DESC",
                (status_filter,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM repairs ORDER BY created_at DESC"
        ).fetchall()


def create_question(question_text: str, telegram_user_id: Optional[int], telegram_username: Optional[str]) -> int:
    with get_db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO questions (question_text, telegram_user_id, telegram_username, status, created_at) VALUES (?, ?, ?, 'new', ?)",
            (question_text, telegram_user_id, telegram_username, utc_now_iso()),
        )
        question_id = int(cur.lastrowid)
        conn.commit()
        return question_id


def answer_question(question_id: int, answer_text: str) -> Optional[sqlite3.Row]:
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM questions WHERE id = ? AND status = 'new'", (question_id,)).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE questions SET status = 'answered', answer_text = ?, answered_at = ? WHERE id = ?",
            (answer_text, utc_now_iso(), question_id),
        )
        conn.commit()
        return row


# --- Prices ---

DEFAULT_PRICES = [
    ("Смартфоны", "Замена дисплея", "от 6 900 ₽", 1),
    ("Смартфоны", "Замена аккумулятора", "от 2 900 ₽", 2),
    ("Смартфоны", "Ремонт разъёма зарядки", "от 2 500 ₽", 3),
    ("Смартфоны", 'Неисправность "не включается"', "от 2 300 ₽", 4),
    ("Ноутбуки", "Замена SSD / установка", "от 1 900 ₽", 5),
    ("Ноутбуки", "Чистка от пыли и термопаста", "от 2 500 ₽", 6),
    ("Ноутбуки", "Ремонт питания / разъёма", "от 2 900 ₽", 7),
    ("Ноутбуки", "Замена клавиатуры", "от 4 900 ₽", 8),
    ("Планшеты", "Замена дисплея", "от 5 500 ₽", 9),
    ("Планшеты", "Замена аккумулятора", "от 2 700 ₽", 10),
    ("Планшеты", "Ремонт кнопок / шлейфов", "от 2 400 ₽", 11),
    ("Прочее", "Диагностика (если ремонт не выполняется)", "1 000 ₽", 12),
    ("Прочее", "Срочная диагностика", "1 800 ₽", 13),
]


def seed_prices_if_empty() -> None:
    with get_db_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO prices (category, service_name, price_text, sort_order) VALUES (?, ?, ?, ?)",
                DEFAULT_PRICES,
            )
            conn.commit()


def get_all_prices() -> List[sqlite3.Row]:
    with get_db_conn() as conn:
        return conn.execute("SELECT * FROM prices ORDER BY sort_order, id").fetchall()


def add_price(category: str, service_name: str, price_text: str, sort_order: int) -> sqlite3.Row:
    with get_db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO prices (category, service_name, price_text, sort_order) VALUES (?, ?, ?, ?)",
            (category, service_name, price_text, sort_order),
        )
        conn.commit()
        return conn.execute("SELECT * FROM prices WHERE id = ?", (cur.lastrowid,)).fetchone()


def update_price(price_id: int, category: str, service_name: str, price_text: str, sort_order: int) -> bool:
    with get_db_conn() as conn:
        conn.execute(
            "UPDATE prices SET category = ?, service_name = ?, price_text = ?, sort_order = ? WHERE id = ?",
            (category, service_name, price_text, sort_order, price_id),
        )
        conn.commit()
        return conn.total_changes > 0


def delete_price(price_id: int) -> bool:
    with get_db_conn() as conn:
        conn.execute("DELETE FROM prices WHERE id = ?", (price_id,))
        conn.commit()
        return conn.total_changes > 0


# --- Time Slots ---

def seed_slots_if_empty(force: bool = False) -> int:
    """Создаёт слоты на следующие 7 рабочих дней если свободных нет.

    Если force=True — всегда генерирует (используется из админки).
    Возвращает количество добавленных слотов.
    """
    if not force:
        with get_db_conn() as conn:
            now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
            count = conn.execute(
                "SELECT COUNT(*) FROM time_slots WHERE is_booked = 0 AND slot_datetime > ?", (now_iso,)
            ).fetchone()[0]
            if count > 0:
                return 0

    now = datetime.now(timezone.utc)
    slots = []
    days_added = 0
    check_date = now.date() + timedelta(days=1)

    while days_added < 7:
        if check_date.weekday() != 6:  # пропускаем воскресенье
            for hour in range(10, 20):
                slot_dt = datetime(
                    check_date.year, check_date.month, check_date.day,
                    hour, 0, 0, tzinfo=timezone.utc,
                )
                slots.append((slot_dt.isoformat(timespec="seconds"), 0, None, utc_now_iso()))
            days_added += 1
        check_date += timedelta(days=1)

    added = 0
    with get_db_conn() as conn:
        for row in slots:
            try:
                conn.execute(
                    "INSERT INTO time_slots (slot_datetime, is_booked, repair_id, created_at) VALUES (?, ?, ?, ?)",
                    row,
                )
                added += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
    return added


def get_available_slots() -> List[sqlite3.Row]:
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_db_conn() as conn:
        return conn.execute(
            "SELECT * FROM time_slots WHERE is_booked = 0 AND slot_datetime > ? ORDER BY slot_datetime LIMIT 60",
            (now_iso,),
        ).fetchall()


def get_all_slots() -> List[sqlite3.Row]:
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_db_conn() as conn:
        return conn.execute(
            "SELECT * FROM time_slots WHERE slot_datetime > ? ORDER BY slot_datetime",
            (now_iso,),
        ).fetchall()


def add_slot(slot_datetime: str) -> Optional[sqlite3.Row]:
    try:
        with get_db_conn() as conn:
            cur = conn.execute(
                "INSERT INTO time_slots (slot_datetime, is_booked, created_at) VALUES (?, 0, ?)",
                (slot_datetime, utc_now_iso()),
            )
            conn.commit()
            return conn.execute("SELECT * FROM time_slots WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        return None


def delete_slot(slot_id: int) -> bool:
    with get_db_conn() as conn:
        conn.execute("DELETE FROM time_slots WHERE id = ? AND is_booked = 0", (slot_id,))
        conn.commit()
        return conn.total_changes > 0
