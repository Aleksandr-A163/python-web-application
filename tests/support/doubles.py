"""Тестовые двойники, изолирующие тесты от времени и консольного ввода."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime

from phonebook.model import Contact


class SequenceClock:
    """Stub Clock: последовательно возвращает заранее заданные даты."""

    def __init__(self, *values: datetime) -> None:
        self._values = iter(values)

    def __call__(self) -> datetime:
        return next(self._values)


class StubView:
    """Spy/Stub представления: выдаёт ответы и запоминает вызовы контроллера."""

    def __init__(self, inputs: list[str] | None = None) -> None:
        self._inputs: Iterator[str] = iter(inputs or [])
        self.messages: list[str] = []
        self.errors: list[str] = []
        self.shown_contacts: list[tuple[Contact, ...]] = []
        self.shown_groups: list[dict[str, tuple[Contact, ...]]] = []
        self.menu_calls = 0

    def show_menu(self) -> None:
        self.menu_calls += 1

    def read(self, prompt: str) -> str:
        return next(self._inputs)

    def show_message(self, message: str) -> None:
        self.messages.append(message)

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def show_contacts(self, contacts: Iterable[Contact]) -> None:
        self.shown_contacts.append(tuple(contacts))

    def show_grouped_contacts(
        self, groups: Mapping[str, tuple[Contact, ...]]
    ) -> None:
        self.shown_groups.append(dict(groups))

    def confirm(self, prompt: str) -> bool:
        return self.read(prompt).lower() in {"д", "да", "y", "yes"}
