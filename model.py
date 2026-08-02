"""Model: contacts, phone book rules, and JSON persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from exceptions import (
    ContactNotFoundError,
    FileReadError,
    FileWriteError,
    InvalidDataFormatError,
    ValidationError,
)


@dataclass
class Contact:
    """A single phone book entry."""

    contact_id: int
    name: str
    phone: str
    comment: str = ""

    def __post_init__(self) -> None:
        try:
            self.contact_id = int(self.contact_id)
        except (TypeError, ValueError) as error:
            raise ValidationError("ID контакта должен быть целым числом.") from error

        self.name = str(self.name).strip()
        self.phone = str(self.phone).strip()
        self.comment = str(self.comment).strip()

        if self.contact_id < 1:
            raise ValidationError("ID контакта должен быть положительным числом.")
        if not self.name:
            raise ValidationError("Имя контакта не должно быть пустым.")
        if not self.phone:
            raise ValidationError("Телефон контакта не должен быть пустым.")

    def to_dict(self) -> dict[str, int | str]:
        return {
            "id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: object) -> Contact:
        if not isinstance(data, dict):
            raise InvalidDataFormatError("Контакт должен быть объектом JSON.")
        try:
            return cls(
                contact_id=data["id"],
                name=data["name"],
                phone=data["phone"],
                comment=data.get("comment", ""),
            )
        except KeyError as error:
            raise InvalidDataFormatError(
                f"В контакте отсутствует обязательное поле: {error.args[0]}."
            ) from error
        except ValidationError as error:
            raise InvalidDataFormatError(str(error)) from error


class PhoneBook:
    """A collection of contacts and operations on it."""

    def __init__(self, contacts: Iterable[Contact] | None = None) -> None:
        self._contacts = list(contacts or [])
        ids = [contact.contact_id for contact in self._contacts]
        if len(ids) != len(set(ids)):
            raise InvalidDataFormatError("В файле обнаружены повторяющиеся ID.")

    @property
    def contacts(self) -> tuple[Contact, ...]:
        return tuple(self._contacts)

    def replace_all(self, contacts: Iterable[Contact]) -> None:
        replacement = PhoneBook(contacts)
        self._contacts = list(replacement.contacts)

    def add_contact(self, name: str, phone: str, comment: str = "") -> Contact:
        contact = Contact(self._get_next_id(), name, phone, comment)
        self._contacts.append(contact)
        return contact

    def find_contacts(self, query: str) -> list[Contact]:
        normalized = str(query).strip().lower()
        if not normalized:
            raise ValidationError("Строка поиска не должна быть пустой.")

        return [
            contact
            for contact in self._contacts
            if any(
                normalized in field.lower()
                for field in (
                    str(contact.contact_id),
                    contact.name,
                    contact.phone,
                    contact.comment,
                )
            )
        ]

    def get_by_id(self, contact_id: int) -> Contact:
        try:
            normalized_id = int(contact_id)
        except (TypeError, ValueError) as error:
            raise ValidationError("ID контакта должен быть целым числом.") from error

        for contact in self._contacts:
            if contact.contact_id == normalized_id:
                return contact
        raise ContactNotFoundError(f"Контакт с ID {normalized_id} не найден.")

    def update_contact(
        self,
        contact_id: int,
        name: str | None = None,
        phone: str | None = None,
        comment: str | None = None,
    ) -> Contact:
        current = self.get_by_id(contact_id)
        updated = Contact(
            current.contact_id,
            current.name if name is None else name,
            current.phone if phone is None else phone,
            current.comment if comment is None else comment,
        )
        current.name = updated.name
        current.phone = updated.phone
        current.comment = updated.comment
        return current

    def delete_contact(self, contact_id: int) -> Contact:
        contact = self.get_by_id(contact_id)
        self._contacts.remove(contact)
        return contact

    def _get_next_id(self) -> int:
        return max((contact.contact_id for contact in self._contacts), default=0) + 1


class FileReader:
    """Reads contacts from a JSON file."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def read(self) -> list[Contact]:
        if not self.file_path.exists():
            return []
        try:
            with self.file_path.open(encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise InvalidDataFormatError("Файл содержит некорректный JSON.") from error
        except OSError as error:
            raise FileReadError(f"Не удалось прочитать файл: {error}.") from error

        if not isinstance(data, list):
            raise InvalidDataFormatError("Файл должен содержать список контактов.")
        return [Contact.from_dict(item) for item in data]


class FileWriter:
    """Writes contacts to a JSON file."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def write(self, contacts: Iterable[Contact]) -> None:
        try:
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(
                    [contact.to_dict() for contact in contacts],
                    file,
                    ensure_ascii=False,
                    indent=2,
                )
        except OSError as error:
            raise FileWriteError(f"Не удалось сохранить файл: {error}.") from error
