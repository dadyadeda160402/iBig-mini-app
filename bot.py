# -*- coding: utf-8 -*-
"""Telegram-бот: обработчики команд, callback-кнопок и текстовых сообщений."""

import asyncio
import json
import hashlib
import hmac
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import ADMIN_CHAT_ID_INT, QUESTIONS_CHAT_ID_INT, BOT_TOKEN, CONFIG_OK
from database.models import answer_question, sanitize_text, update_repair_status_by_order as update_repair_status

# Для ответа администратора на вопросы в Telegram:
# admin_chat_id -> question_id
pending_admin_replies: Dict[int, int] = {}

# Экземпляр Application (создаётся при инициализации)
application: Optional[Application] = None

if CONFIG_OK:
    application = Application.builder().token(BOT_TOKEN).concurrent_updates(False).build()


def run_async(coro):
    """Запускает coroutine в контексте синхронного Flask handler."""
    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(coro)
    except RuntimeError:
        return asyncio.run(coro)


def parse_telegram_webapp_init_data(init_data: str) -> Tuple[bool, Dict[str, str]]:
    """Парсит initData из Telegram Web Apps и валидирует подпись."""
    if not init_data or not isinstance(init_data, str):
        return False, {}

    params_raw = parse_qs(init_data, keep_blank_values=True)
    params: Dict[str, str] = {}
    for k, v in params_raw.items():
        if not v:
            continue
        params[k] = v[0]

    provided_hash = params.get("hash")
    if not provided_hash:
        return False, {}

    check_items = [(k, params[k]) for k in params.keys() if k != "hash" and k in params]
    check_items.sort(key=lambda x: x[0])
    check_string = "\n".join([f"{k}={v}" for k, v in check_items])

    secret_key = hmac.new("WebAppData".encode(), BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    ok = hmac.compare_digest(computed_hash, provided_hash)
    return ok, params


def extract_user_from_init_data(init_params: Dict[str, str]) -> Tuple[Optional[int], Optional[str]]:
    """Извлекает telegram_user_id и telegram_username из initData."""
    user_str = init_params.get("user")
    if not user_str:
        return None, None
    try:
        user = json.loads(user_str)
        user_id = user.get("id")
        username = user.get("username")
        if username:
            username = f"@{username}"
        return user_id, username
    except Exception:
        return None, None


async def notify_admin_new_repair(row) -> None:
    """Отправляет администратору уведомление о новой заявке на ремонт."""
    device_info = row["device_type"]
    if row["device_model"]:
        device_info += f" {row['device_model']}"
    text = (
        "📋 Новая запись на ремонт\n"
        f"Номер заявки: {row['order_number']}\n"
        f"Клиент: {row['name']} ({row['phone']})\n"
        f"Устройство: {device_info}\n"
        f"Проблема: {row['description']}\n"
        f"Время: {row['preferred_time']}\n"
    )
    await application.bot.send_message(chat_id=ADMIN_CHAT_ID_INT, text=text)


async def notify_admin_new_question(question_id: int, question_text: str, username: str, user_id: Optional[int]) -> None:
    """Отправляет администратору уведомление о новом вопросе."""
    user_line = f"{username or 'без username'}"
    if user_id:
        user_line += f" (id: {user_id})"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Ответить",
                    callback_data=f"reply:{question_id}",
                )
            ]
        ]
    )
    text = (
        "💬 Новый вопрос\n"
        f"Вопрос №: {question_id}\n"
        f"Клиент: {user_line}\n\n"
        f"{question_text}"
    )
    await application.bot.send_message(chat_id=QUESTIONS_CHAT_ID_INT, text=text, reply_markup=keyboard)


async def _handle_admin_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия кнопки «Ответить» администратором."""
    query = update.callback_query
    if not query:
        return

    chat_id = update.effective_chat.id if update.effective_chat else None
    allowed_chats = {ADMIN_CHAT_ID_INT, QUESTIONS_CHAT_ID_INT}
    if chat_id not in allowed_chats:
        await query.answer("Недостаточно прав.", show_alert=True)
        return

    data = query.data or ""
    if not data.startswith("reply:"):
        await query.answer()
        return

    try:
        question_id = int(data.split(":", 1)[1])
    except Exception:
        await query.answer("Некорректный id.", show_alert=True)
        return

    pending_admin_replies[chat_id] = question_id
    await query.answer("Ок. Введите ответ сообщением.")
    await query.message.reply_text(
        "Введите ответ клиенту одним сообщением. После отправки я пересылаю ответ клиенту."
    )


async def _handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений от администратора (ответы на вопросы)."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    allowed_chats = {ADMIN_CHAT_ID_INT, QUESTIONS_CHAT_ID_INT}
    if chat_id not in allowed_chats:
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    if text.lower() in {"cancel", "/cancel", "отмена"}:
        pending_admin_replies.pop(chat_id, None)
        await update.message.reply_text("Ответ отменён.")
        return

    if chat_id not in pending_admin_replies:
        return  # В чате с вопросами молчим, если нет активного ответа

    question_id = pending_admin_replies.get(chat_id)
    if not question_id:
        pending_admin_replies.pop(chat_id, None)
        await update.message.reply_text("Не нашёл активный вопрос. Попробуйте снова.")
        return

    row = answer_question(question_id, text)
    if not row:
        pending_admin_replies.pop(chat_id, None)
        await update.message.reply_text("Вопрос уже обработан или не найден.")
        return

    user_id = row["telegram_user_id"]
    pending_admin_replies.pop(chat_id, None)

    try:
        await application.bot.send_message(chat_id=user_id, text=f"Здравствуйте! Ответ на ваш вопрос:\n\n{text}")
        await update.message.reply_text("Ответ отправлен клиенту в Telegram.")
    except Exception as e:
        await update.message.reply_text(f"Не удалось отправить клиенту: {e}")


async def _admin_set_repair_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда админа: /setstatus <order_number> <status>"""
    if not update.effective_chat:
        return
    if update.effective_chat.id != ADMIN_CHAT_ID_INT:
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Использование: /setstatus <order_number> <new|in_progress|ready|done>\n"
            "Пример: /setstatus iBig-20260323-ABC123 ready"
        )
        return

    order_number = sanitize_text(args[0], 100)
    status = sanitize_text(args[1], 50)
    allowed = {"new", "in_progress", "ready", "done"}
    if status not in allowed:
        await update.message.reply_text(f"Неизвестный статус. Допустимые: {', '.join(sorted(allowed))}")
        return

    if not update_repair_status(order_number, status):
        await update.message.reply_text("Заявка не найдена по этому номеру.")
        return

    await update.message.reply_text(f"Ок! Статус заявки {order_number} обновлён на: {status}")


def register_bot_handlers() -> None:
    """Регистрирует все обработчики бота."""
    if application is None:
        return
    application.add_handler(CallbackQueryHandler(_handle_admin_reply_callback, pattern=r"^reply:\d+$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_admin_text))
    application.add_handler(CommandHandler("setstatus", _admin_set_repair_status))


def set_webhook_if_needed(webhook_url: str) -> None:
    """Устанавливает Telegram webhook в фоновом потоке, чтобы не блокировать gunicorn."""
    if not webhook_url or application is None:
        return
    url = webhook_url.rstrip("/") + "/telegram-webhook"

    def _set():
        try:
            asyncio.run(application.bot.set_webhook(url=url))
            print(f"[INFO] Telegram webhook установлен: {url}")
        except Exception as e:
            print(f"[WARN] Не удалось установить Telegram webhook: {e}")

    import threading
    threading.Thread(target=_set, daemon=True).start()
