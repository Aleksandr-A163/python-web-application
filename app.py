"""Совместимая ASGI-точка входа для команды ``uvicorn app:app``."""

from phonebook.web.application import app, create_app


__all__ = ["app", "create_app"]
