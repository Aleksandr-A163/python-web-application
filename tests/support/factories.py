"""Фабрики тестовых объектов с безопасными значениями по умолчанию."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from controller import PhoneBookController
from generator import ContactGenerator
from model import Contact, FileReader, FileWriter, PhoneBook
from tests.support.doubles import StubView

ControllerFactory = Callable[
    [list[str] | None, PhoneBook | None],
    tuple[PhoneBookController, StubView],
]


def make_contact(
    contact_id: int = 1,
    name: str = "Иван",
    phone: str = "111",
    comment: str = "",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Contact:
    """Object Mother: создаёт валидный контакт, меняя только важные поля."""

    created = created_at or datetime(2026, 1, 1)
    return Contact(
        contact_id,
        name,
        phone,
        comment,
        created,
        updated_at or created,
    )


def make_controller(
    tmp_path: Path,
    inputs: list[str] | None = None,
    phonebook: PhoneBook | None = None,
) -> tuple[PhoneBookController, StubView]:
    """Fixture Factory: собирает изолированный контроллер и его Spy View."""

    path = tmp_path / "contacts.json"
    view = StubView(inputs)
    controller = PhoneBookController(
        phonebook=phonebook or PhoneBook(),
        reader=FileReader(path),
        writer=FileWriter(path),
        view=view,
        generator=ContactGenerator(seed=42),
    )
    return controller, view
