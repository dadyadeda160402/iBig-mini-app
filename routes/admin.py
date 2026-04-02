# -*- coding: utf-8 -*-
"""Админские эндпоинты: Telegram webhook и служебные проверки."""

from flask import Blueprint, jsonify, request
from telegram import Update

from bot import application, run_async
from config import CONFIG_OK, CONFIG_ERROR

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/health")
def health():
    """Проверка, что процесс жив (удобно для Railway и отладки)."""
    body = {"ok": True}
    if not CONFIG_OK:
        body["config_ok"] = False
        body["hint"] = CONFIG_ERROR
    else:
        body["config_ok"] = True
    return jsonify(body)


@admin_bp.post("/telegram-webhook")
def telegram_webhook():
    """Обработка входящих обновлений от Telegram Bot API."""
    if not CONFIG_OK or application is None:
        return jsonify({"ok": True})

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"ok": True})

    try:
        update = Update.de_json(data, application.bot)
    except Exception:
        return jsonify({"ok": True})

    async def _process():
        await application.process_update(update)

    run_async(_process())
    return jsonify({"ok": True})
