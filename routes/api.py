# -*- coding: utf-8 -*-
"""API-эндпоинты для Mini App."""

from flask import Blueprint, jsonify, request

from bot import (
    notify_admin_new_question,
    notify_admin_new_repair,
    parse_telegram_webapp_init_data,
    extract_user_from_init_data,
    run_async,
    application,
)
from config import CONFIG_OK
from database.models import (
    create_question,
    create_repair,
    get_repair_by_order_number,
    sanitize_phone,
    sanitize_text,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/repair/register")
def api_repair_register():
    """Регистрация заявки на ремонт."""
    if not CONFIG_OK or application is None:
        return jsonify(
            {"ok": False, "error": "Сервер не настроен: задайте BOT_TOKEN и ADMIN_CHAT_ID в Railway Variables."}
        ), 503

    payload = request.get_json(silent=True) or {}
    init_data = payload.get("initData", "")
    ok, init_params = parse_telegram_webapp_init_data(init_data)
    if not ok:
        return jsonify({"ok": False, "error": "Неверный initData Telegram"}), 400

    user_id, _username = extract_user_from_init_data(init_params)

    name = sanitize_text(payload.get("name"), 200)
    phone = sanitize_phone(payload.get("phone"), 50)
    device_type = sanitize_text(payload.get("deviceType"), 200)
    description = sanitize_text(payload.get("description"), 2000)
    preferred_time = sanitize_text(payload.get("preferredTime"), 200)

    if not name or not phone or not device_type or not description or not preferred_time:
        return jsonify({"ok": False, "error": "Заполните все поля"}), 400

    row = create_repair(name, phone, device_type, description, preferred_time, user_id)
    if not row:
        return jsonify({"ok": False, "error": "Не удалось создать заявку"}), 500

    run_async(notify_admin_new_repair(row))
    return jsonify({"ok": True, "order_number": row["order_number"]})


@api_bp.post("/repair/status")
def api_repair_status():
    """Проверка статуса заявки на ремонт."""
    payload = request.get_json(silent=True) or {}
    order_number = sanitize_text(payload.get("orderNumber"), 100)
    if not order_number:
        return jsonify({"ok": False, "error": "Введите номер заявки"}), 400

    row = get_repair_by_order_number(order_number)
    if not row:
        return jsonify({"ok": False, "error": "Заявка не найдена"}), 404

    status = row["status"]
    status_map = {
        "new": "Принята в работу",
        "in_progress": "В ремонте",
        "ready": "Готово к выдаче",
        "done": "Завершено",
    }
    status_ui = status_map.get(status, status)

    return jsonify({"ok": True, "order_number": row["order_number"], "status": status_ui})


@api_bp.post("/question/ask")
def api_question_ask():
    """Отправка вопроса администратору."""
    if not CONFIG_OK or application is None:
        return jsonify(
            {"ok": False, "error": "Сервер не настроен: задайте BOT_TOKEN и ADMIN_CHAT_ID в Railway Variables."}
        ), 503

    payload = request.get_json(silent=True) or {}
    init_data = payload.get("initData", "")
    ok, init_params = parse_telegram_webapp_init_data(init_data)
    if not ok:
        return jsonify({"ok": False, "error": "Неверный initData Telegram"}), 400

    user_id, username = extract_user_from_init_data(init_params)
    if not user_id:
        return jsonify({"ok": False, "error": "Не удалось определить пользователя Telegram"}), 400

    question_text = sanitize_text(payload.get("questionText"), 2000)
    if not question_text:
        return jsonify({"ok": False, "error": "Введите вопрос"}), 400

    question_id = create_question(question_text, user_id, username)
    run_async(notify_admin_new_question(question_id, question_text, username or "", user_id))
    return jsonify({"ok": True, "question_id": question_id})
