"""Тесты бизнес-операций коллекции PhoneBook."""

from datetime import datetime, timedelta

import pytest

from exceptions import ContactNotFoundError, InvalidDataFormatError, ValidationError
from model import PhoneBook
from tests.support.doubles import SequenceClock
from tests.support.factories import make_contact


@pytest.mark.parametrize(
    ("name", "phone", "expected_name", "expected_phone"),
    [
        ("Иван", "+7 999 000-00-01", "Иван", "+7 999 000-00-01"),
        ("  Анна-Мария  ", "  8(999)0000002  ", "Анна-Мария", "8(999)0000002"),
    ],
)
def test_add_contact_accepts_representative_formats(
    name: str, phone: str, expected_name: str, expected_phone: str
) -> None:
    """Классы эквивалентности: обычные и форматированные имя/телефон."""

    contact = PhoneBook().add_contact(name, phone, "  заметка  ")

    assert contact.contact_id == 1
    assert (contact.name, contact.phone, contact.comment) == (
        expected_name,
        expected_phone,
        "заметка",
    )


def test_add_contact_uses_next_id_and_clock() -> None:
    """Новый контакт получает следующий ID и время из внедрённых часов."""

    now = datetime(2026, 8, 22, 12)
    phonebook = PhoneBook([make_contact(contact_id=3)], clock=lambda: now)

    contact = phonebook.add_contact("Анна", "222")

    assert contact.contact_id == 4
    assert contact.created_at == contact.updated_at == now


def test_add_contact_rejects_empty_required_fields() -> None:
    """Классы эквивалентности: отсутствует имя или телефон."""

    for name, phone in [("   ", "123"), ("Иван", "   ")]:
        with pytest.raises(ValidationError):
            PhoneBook().add_contact(name, phone)


def test_find_contacts_searches_every_field() -> None:
    """Таблица решений проверяет имя, телефон, комментарий, ID и отсутствие результата."""

    phonebook = PhoneBook()
    phonebook.add_contact("Иван Петров", "+79990000001", "друг")
    phonebook.add_contact("Анна", "+79990000002", "работа")
    cases = {
        "ПЕТРОВ": ["Иван Петров"],
        "0002": ["Анна"],
        "работа": ["Анна"],
        "2": ["Анна"],
        "нет такого": [],
    }

    for query, expected in cases.items():
        result = [contact.name for contact in phonebook.find_contacts(query)]
        assert result == expected


def test_find_contacts_rejects_blank_query() -> None:
    """Пробелы представляют эквивалентный класс пустых поисковых запросов."""

    with pytest.raises(ValidationError, match="поиска"):
        PhoneBook().find_contacts("   ")


def test_search_cache_is_used_and_invalidated_by_mutations() -> None:
    """Переходы состояний: кэш очищается после add, update и delete."""

    phonebook = PhoneBook()
    first = phonebook.add_contact("Иван", "111")
    phonebook.find_contacts("иван")
    phonebook.find_contacts("иван")
    assert phonebook.search_cache_info().hits == 1

    phonebook.add_contact("Анна", "222")
    assert phonebook.search_cache_info().currsize == 0
    phonebook.find_contacts("иван")
    phonebook.update_contact(first.contact_id, comment="друг")
    assert phonebook.search_cache_info().currsize == 0
    phonebook.find_contacts("иван")
    phonebook.delete_contact(first.contact_id)
    assert phonebook.search_cache_info().currsize == 0


def test_update_contact_changes_selected_fields_and_date() -> None:
    """Изменяются только переданные поля и updated_at, но не created_at."""

    created = datetime(2026, 8, 22, 10)
    updated = created + timedelta(hours=2)
    phonebook = PhoneBook(clock=SequenceClock(created, updated))
    contact = phonebook.add_contact("Иван", "111", "старый")

    result = phonebook.update_contact(contact.contact_id, name="Пётр", phone="222")

    assert result is contact
    assert (contact.name, contact.phone, contact.comment) == ("Пётр", "222", "старый")
    assert contact.created_at == created
    assert contact.updated_at == updated


def test_update_contact_rejects_empty_required_fields() -> None:
    """Имя и телефон принадлежат одному классу обязательных полей."""

    for field in ("name", "phone"):
        phonebook = PhoneBook([make_contact()])
        with pytest.raises(ValidationError):
            phonebook.update_contact(1, **{field: "   "})


def test_delete_contact_returns_removed_entity() -> None:
    """Успешное удаление возвращает контакт и очищает справочник."""

    phonebook = PhoneBook([make_contact()])

    deleted = phonebook.delete_contact(1)

    assert deleted.name == "Иван"
    assert phonebook.contacts == ()


def test_delete_contact_rejects_missing_ids() -> None:
    """Границы: ID 0 и отсутствующий положительный ID дают одну доменную ошибку."""

    for contact_id in (0, 999):
        with pytest.raises(ContactNotFoundError):
            PhoneBook().delete_contact(contact_id)


def test_get_by_id_rejects_non_integer_value() -> None:
    """Строка без числа представляет класс ID неверного типа."""

    with pytest.raises(ValidationError, match="целым"):
        PhoneBook().get_by_id("abc")  # type: ignore[arg-type]


def test_grouping_sorts_contacts_by_first_letter() -> None:
    """Группы и контакты внутри них возвращаются в алфавитном порядке."""

    phonebook = PhoneBook(
        [
            make_contact(1, "Ирина", "1"),
            make_contact(2, "Анна", "2"),
            make_contact(3, "Иван", "3"),
        ]
    )

    groups = phonebook.group_by_first_letter()

    assert list(groups) == ["А", "И"]
    assert [item.name for item in groups["И"]] == ["Иван", "Ирина"]


def test_replace_all_rejects_duplicate_ids() -> None:
    """Инвариант коллекции запрещает повторяющиеся идентификаторы."""

    duplicate_contacts = [make_contact(1), make_contact(1, "Анна", "2")]

    with pytest.raises(InvalidDataFormatError, match="повторяющиеся"):
        PhoneBook().replace_all(duplicate_contacts)
