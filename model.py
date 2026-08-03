"""Модель: контакты, логика справочника и хранение данных в JSON."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from itertools import groupby
from pathlib import Path
from typing import NamedTuple, TypeAlias

from exceptions import (
    ContactNotFoundError,
    FileReadError,
    FileWriteError,
    InvalidDataFormatError,
    ValidationError,
)


@dataclass
class Contact:
    """Одна запись телефонного справочника."""

    contact_id: int
    name: str
    phone: str
    comment: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        try:
            self.contact_id = int(self.contact_id)
        except (TypeError, ValueError) as error:
            raise ValidationError("ID контакта должен быть целым числом.") from error

        self.name = str(self.name).strip()
        self.phone = str(self.phone).strip()
        self.comment = str(self.comment).strip()

        if not isinstance(self.created_at, datetime):
            raise ValidationError("Дата создания контакта имеет неверный формат.")
        if not isinstance(self.updated_at, datetime):
            raise ValidationError("Дата изменения контакта имеет неверный формат.")

        if self.contact_id < 1:
            raise ValidationError("ID контакта должен быть положительным числом.")
        if not self.name:
            raise ValidationError("Имя контакта не должно быть пустым.")
        if not self.phone:
            raise ValidationError("Телефон контакта не должен быть пустым.")

    def to_dict(self) -> ContactData:
        return {
            "id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: object) -> Contact:
        if not isinstance(data, dict):
            raise InvalidDataFormatError("Контакт должен быть объектом JSON.")
        try:
            created_at = cls._parse_datetime(data.get("created_at"))
            updated_at = cls._parse_datetime(data.get("updated_at"))
            if created_at is None:
                created_at = datetime.now()
            if updated_at is None:
                updated_at = created_at
            return cls(
                contact_id=int(data["id"]),
                name=str(data["name"]),
                phone=str(data["phone"]),
                comment=str(data.get("comment", "")),
                created_at=created_at,
                updated_at=updated_at,
            )
        except KeyError as error:
            raise InvalidDataFormatError(
                f"В контакте отсутствует обязательное поле: {error.args[0]}."
            ) from error
        except (TypeError, ValueError) as error:
            raise InvalidDataFormatError(
                "Поля контакта имеют неверные типы данных."
            ) from error
        except ValidationError as error:
            raise InvalidDataFormatError(str(error)) from error

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidDataFormatError("Дата контакта должна быть строкой.")
        try:
            return datetime.fromisoformat(value)
        except ValueError as error:
            raise InvalidDataFormatError(
                f"Дата контакта имеет неверный формат: {value}."
            ) from error


ContactData: TypeAlias = dict[str, int | str]
ContactGroups: TypeAlias = dict[str, tuple[Contact, ...]]


class SearchCacheInfo(NamedTuple):
    """Типизированная статистика кэша поиска."""

    hits: int
    misses: int
    maxsize: int | None
    currsize: int


class PhoneBook:
    """Коллекция контактов и операции над ней."""

    def __init__(
        self,
        contacts: Iterable[Contact] | None = None,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._contacts = list(contacts or [])
        self._clock = clock
        self.clear_search_cache()
        ids = [contact.contact_id for contact in self._contacts]
        if len(ids) != len(set(ids)):
            raise InvalidDataFormatError("В файле обнаружены повторяющиеся ID.")

    @property
    def contacts(self) -> tuple[Contact, ...]:
        return tuple(self._contacts)

    def replace_all(self, contacts: Iterable[Contact]) -> None:
        replacement = PhoneBook(contacts, clock=self._clock)
        self._contacts = list(replacement.contacts)
        self.clear_search_cache()

    def add_contact(self, name: str, phone: str, comment: str = "") -> Contact:
        now = self._clock()
        contact = Contact(
            self._get_next_id(),
            name,
            phone,
            comment,
            created_at=now,
            updated_at=now,
        )
        self._contacts.append(contact)
        self.clear_search_cache()
        return contact

    def find_contacts(self, query: str) -> list[Contact]:
        normalized = str(query).strip().lower()
        if not normalized:
            raise ValidationError("Строка поиска не должна быть пустой.")

        return list(self._cached_find(normalized))

    @lru_cache(maxsize=128)
    def _cached_find(self, normalized: str) -> tuple[Contact, ...]:
        return tuple(
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
        )

    def clear_search_cache(self) -> None:
        self._cached_find.cache_clear()

    def search_cache_info(self) -> SearchCacheInfo:
        """Возвращает статистику кэша поиска для диагностики и тестов."""

        info = self._cached_find.cache_info()
        return SearchCacheInfo(
            hits=info.hits,
            misses=info.misses,
            maxsize=info.maxsize,
            currsize=info.currsize,
        )

    def group_by_first_letter(self) -> ContactGroups:
        sorted_contacts = sorted(
            self._contacts,
            key=lambda contact: contact.name.casefold(),
        )
        return {
            letter: tuple(contacts)
            for letter, contacts in groupby(
                sorted_contacts,
                key=lambda contact: contact.name[0].upper(),
            )
        }

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
            created_at=current.created_at,
            updated_at=self._clock(),
        )
        current.name = updated.name
        current.phone = updated.phone
        current.comment = updated.comment
        current.updated_at = updated.updated_at
        self.clear_search_cache()
        return current

    def delete_contact(self, contact_id: int) -> Contact:
        contact = self.get_by_id(contact_id)
        self._contacts.remove(contact)
        self.clear_search_cache()
        return contact

    def _get_next_id(self) -> int:
        return max((contact.contact_id for contact in self._contacts), default=0) + 1


class FileReader:
    """Читает контакты из JSON-файла."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path: Path = Path(file_path)

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
    """Записывает контакты в JSON-файл."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path: Path = Path(file_path)

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
