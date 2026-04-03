# -*- coding: utf-8 -*-
"""Админские эндпоинты: Telegram webhook, health, управление ценами и слотами."""

from flask import Blueprint, jsonify, request, render_template, abort
from telegram import Update

from bot import application, run_async
from config import CONFIG_OK, CONFIG_ERROR, ADMIN_TOKEN
from database.models import (
    get_all_prices, add_price, update_price, delete_price,
    get_all_slots, add_slot, delete_slot, seed_slots_if_empty, sanitize_text,
    get_all_repairs, update_repair_status,
)

admin_bp = Blueprint("admin", __name__)


def _check_token() -> bool:
    if not ADMIN_TOKEN:
        return False
    token = request.args.get("token", "") or request.headers.get("X-Admin-Token", "")
    if not token and request.is_json:
        token = (request.get_json(silent=True) or {}).get("token", "")
    return token == ADMIN_TOKEN


@admin_bp.get("/health")
def health():
    body = {"ok": True}
    if not CONFIG_OK:
        body["config_ok"] = False
        body["hint"] = CONFIG_ERROR
    else:
        body["config_ok"] = True
    return jsonify(body)


@admin_bp.post("/telegram-webhook")
def telegram_webhook():
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


# --- Admin Panel ---

@admin_bp.get("/admin")
def admin_panel():
    if not _check_token():
        abort(403)
    return render_template("admin.html", token=request.args.get("token", ""))


# --- Prices API ---

@admin_bp.get("/api/admin/prices")
def api_admin_prices_list():
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    prices = get_all_prices()
    return jsonify({"ok": True, "prices": [dict(p) for p in prices]})


@admin_bp.post("/api/admin/prices")
def api_admin_prices_add():
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    category = sanitize_text(payload.get("category"), 100)
    service_name = sanitize_text(payload.get("service_name"), 200)
    price_text = sanitize_text(payload.get("price_text"), 100)
    sort_order = int(payload.get("sort_order", 99))
    if not category or not service_name or not price_text:
        return jsonify({"ok": False, "error": "Заполните все поля"}), 400
    row = add_price(category, service_name, price_text, sort_order)
    return jsonify({"ok": True, "price": dict(row)})


@admin_bp.put("/api/admin/prices/<int:price_id>")
def api_admin_prices_update(price_id):
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    category = sanitize_text(payload.get("category"), 100)
    service_name = sanitize_text(payload.get("service_name"), 200)
    price_text = sanitize_text(payload.get("price_text"), 100)
    sort_order = int(payload.get("sort_order", 99))
    if not category or not service_name or not price_text:
        return jsonify({"ok": False, "error": "Заполните все поля"}), 400
    ok = update_price(price_id, category, service_name, price_text, sort_order)
    return jsonify({"ok": ok})


@admin_bp.delete("/api/admin/prices/<int:price_id>")
def api_admin_prices_delete(price_id):
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    ok = delete_price(price_id)
    return jsonify({"ok": ok})


# --- Slots API ---

@admin_bp.get("/api/admin/slots")
def api_admin_slots_list():
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    slots = get_all_slots()
    return jsonify({"ok": True, "slots": [dict(s) for s in slots]})


@admin_bp.post("/api/admin/slots")
def api_admin_slots_add():
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    slot_datetime = sanitize_text(payload.get("slot_datetime"), 50)
    if not slot_datetime:
        return jsonify({"ok": False, "error": "Укажите дату и время"}), 400
    row = add_slot(slot_datetime)
    if not row:
        return jsonify({"ok": False, "error": "Такой слот уже существует"}), 409
    return jsonify({"ok": True, "slot": dict(row)})


@admin_bp.delete("/api/admin/slots/<int:slot_id>")
def api_admin_slots_delete(slot_id):
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    ok = delete_slot(slot_id)
    return jsonify({"ok": ok})


@admin_bp.post("/api/admin/slots/generate")
def api_admin_slots_generate():
    """Авто-генерация слотов на 7 дней вперёд (пн–сб, 10:00–19:00)."""
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    added = seed_slots_if_empty(force=True)
    return jsonify({"ok": True, "added": added})


# --- Repairs API (admin) ---

@admin_bp.get("/api/admin/repairs")
def api_admin_repairs_list():
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    status_filter = request.args.get("status", "")
    repairs = get_all_repairs(status_filter or None)
    return jsonify({"ok": True, "repairs": [dict(r) for r in repairs]})


@admin_bp.put("/api/admin/repairs/<int:repair_id>/status")
def api_admin_repairs_status(repair_id):
    if not _check_token():
        return jsonify({"ok": False, "error": "Forbidden"}), 403
    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status", "")
    allowed = {"new", "in_progress", "ready", "done"}
    if new_status not in allowed:
        return jsonify({"ok": False, "error": "Недопустимый статус"}), 400
    ok = update_repair_status(repair_id, new_status)
    return jsonify({"ok": ok})
