"""Зависимости веб-интерфейса и JSON API."""

from collections.abc import Iterable
from typing import Protocol

from fastapi import Request

from model import Contact, PhoneBook


class ContactWriter(Protocol):
    """Минимальный контракт механизма сохранения контактов."""

    def write(self, contacts: Iterable[Contact]) -> None:
        """Сохраняет полное актуальное состояние справочника."""


def get_phonebook(request: Request) -> PhoneBook:
    """Возвращает справочник, принадлежащий экземпляру приложения."""

    return request.app.state.phonebook


def get_writer(request: Request) -> ContactWriter:
    """Возвращает настроенный механизм сохранения контактов."""

    return request.app.state.writer
