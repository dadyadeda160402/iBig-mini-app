# -*- coding: utf-8 -*-
"""Точка входа: Flask-приложение, регистрация blueprints, запуск."""

import os

from flask import Flask, render_template

from config import CONFIG_OK, CONFIG_ERROR, WEBHOOK_URL
from database.db import init_db
from bot import register_bot_handlers, set_webhook_if_needed
from routes.api import api_bp
from routes.admin import admin_bp

app = Flask(__name__)


@app.get("/")
def index():
    """Главная страница Mini App."""
    return render_template("index.html")


# Регистрация blueprints
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)


_startup_done = False


def startup() -> None:
    """Инициализация БД, бота и webhook при старте приложения."""
    global _startup_done
    if _startup_done:
        return
    init_db()
    from database.models import seed_prices_if_empty, seed_slots_if_empty
    seed_prices_if_empty()
    seed_slots_if_empty()
    if not CONFIG_OK:
        print(f"[WARN] Конфигурация бота неполная: {CONFIG_ERROR} Страница / откроется, но API и уведомления не работают.")
    register_bot_handlers()
    set_webhook_if_needed(WEBHOOK_URL)
    _startup_done = True


# Важно для Railway + gunicorn: gunicorn запускает объект Flask,
# а не вызывает main(). Поэтому стартуем при импорте модуля.
startup()


def main() -> None:
    """Локальный запуск Flask-сервера."""
    startup()
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
