"""Тесты сущности Contact и её JSON-представления."""

from datetime import datetime

import pytest

from exceptions import InvalidDataFormatError, ValidationError
from model import Contact
from tests.support.factories import make_contact


def test_contact_rejects_invalid_id_classes() -> None:
    """Граница 0 и неверный тип представляют два класса невалидных ID."""

    for bad_id in (0, "abc"):
        with pytest.raises(ValidationError):
            Contact(bad_id, "Иван", "111")  # type: ignore[arg-type]


def test_contact_rejects_invalid_dates() -> None:
    """Оба временных поля должны содержать объекты datetime."""

    for field in ("created_at", "updated_at"):
        with pytest.raises(ValidationError, match="Дата"):
            Contact(1, "Иван", "111", **{field: "2026-01-01"})  # type: ignore[arg-type]


def test_contact_serialization_round_trip() -> None:
    """Преобразование Contact → dict → Contact не теряет данные."""

    contact = make_contact(
        comment="друг",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 2, 2),
    )

    restored = Contact.from_dict(contact.to_dict())

    assert restored == contact


def test_contact_from_dict_rejects_invalid_data_classes() -> None:
    """Представители классов проверяют структуру, поля, типы и даты входных данных."""

    invalid_data = [
        None,
        {"phone": "111"},
        {"id": 1, "name": "Иван"},
        {"id": "bad", "name": "Иван", "phone": "111"},
        {"id": 1, "name": "", "phone": "111"},
        {"id": 1, "name": "Иван", "phone": "111", "created_at": 123},
        {"id": 1, "name": "Иван", "phone": "111", "updated_at": "not-a-date"},
    ]

    for data in invalid_data:
        with pytest.raises(InvalidDataFormatError):
            Contact.from_dict(data)
