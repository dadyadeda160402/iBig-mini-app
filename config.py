# -*- coding: utf-8 -*-
"""Конфигурация приложения: токены, пути, переменные окружения."""

import os
from typing import Optional

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID: str = os.getenv("ADMIN_CHAT_ID", "").strip()
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "").strip()

ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "").strip()

# Отдельный чат для вопросов клиентов (опционально).
# Если не задан — вопросы идут в ADMIN_CHAT_ID.
QUESTIONS_CHAT_ID: str = os.getenv("QUESTIONS_CHAT_ID", "").strip()

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH: str = os.path.join(BASE_DIR, "database.db")

# Валидация конфигурации
CONFIG_OK: bool = False
CONFIG_ERROR: str = ""
ADMIN_CHAT_ID_INT: int = 0
QUESTIONS_CHAT_ID_INT: int = 0

if not BOT_TOKEN:
    CONFIG_ERROR = "BOT_TOKEN не задан в переменных окружения Railway."
elif not ADMIN_CHAT_ID:
    CONFIG_ERROR = "ADMIN_CHAT_ID не задан в переменных окружения Railway."
else:
    try:
        ADMIN_CHAT_ID_INT = int(ADMIN_CHAT_ID)
        CONFIG_OK = True
        # Если задан отдельный чат для вопросов — используем его, иначе главный чат
        if QUESTIONS_CHAT_ID:
            QUESTIONS_CHAT_ID_INT = int(QUESTIONS_CHAT_ID)
        else:
            QUESTIONS_CHAT_ID_INT = ADMIN_CHAT_ID_INT
    except ValueError:
        CONFIG_ERROR = "ADMIN_CHAT_ID / QUESTIONS_CHAT_ID должны быть целыми числами."
