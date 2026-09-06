"""Зависимости веб-интерфейса и JSON API."""

from fastapi import Request

from model import FileWriter, PhoneBook


def get_phonebook(request: Request) -> PhoneBook:
    """Возвращает справочник, принадлежащий экземпляру приложения."""

    return request.app.state.phonebook


def get_writer(request: Request) -> FileWriter:
    """Возвращает настроенный механизм сохранения контактов."""

    return request.app.state.writer
