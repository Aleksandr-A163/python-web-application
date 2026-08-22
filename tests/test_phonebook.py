"""Полный набор тестов телефонного справочника."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import main as application
from controller import PhoneBookController
from exceptions import (
    ContactNotFoundError,
    FileReadError,
    FileWriteError,
    InvalidDataFormatError,
    ValidationError,
)
from generator import ContactGenerator
from model import Contact, FileReader, FileWriter, PhoneBook
from view import ConsoleView


class SequenceClock:
    def __init__(self, *values: datetime) -> None:
        self._values = iter(values)

    def __call__(self) -> datetime:
        return next(self._values)


class StubView:
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

    def show_contacts(self, contacts: object) -> None:
        self.shown_contacts.append(tuple(contacts))  # type: ignore[arg-type]

    def show_grouped_contacts(self, groups: object) -> None:
        self.shown_groups.append(dict(groups))  # type: ignore[arg-type]

    def confirm(self, prompt: str) -> bool:
        return self.read(prompt).lower() in {"д", "да", "y", "yes"}


def make_controller(
    tmp_path: Path,
    inputs: list[str] | None = None,
    phonebook: PhoneBook | None = None,
) -> tuple[PhoneBookController, StubView]:
    path = tmp_path / "contacts.json"
    view = StubView(inputs)
    controller = PhoneBookController(
        phonebook=phonebook or PhoneBook(),
        reader=FileReader(path),
        writer=FileWriter(path),
        view=view,  # type: ignore[arg-type]
        generator=ContactGenerator(seed=42),
    )
    return controller, view


@pytest.mark.parametrize(
    ("name", "phone", "expected_name", "expected_phone"),
    [
        ("Иван", "+7 999 000-00-01", "Иван", "+7 999 000-00-01"),
        ("  Анна-Мария  ", "  8(999)0000002  ", "Анна-Мария", "8(999)0000002"),
    ],
)
def test_add_contact_accepts_name_and_phone_formats(
    name: str, phone: str, expected_name: str, expected_phone: str
) -> None:
    contact = PhoneBook().add_contact(name, phone, "  заметка  ")
    assert contact.contact_id == 1
    assert (contact.name, contact.phone, contact.comment) == (
        expected_name,
        expected_phone,
        "заметка",
    )


def test_add_contact_uses_next_id_and_dates() -> None:
    now = datetime(2026, 8, 22, 12, 0)
    phonebook = PhoneBook([Contact(3, "Иван", "111")], clock=lambda: now)
    contact = phonebook.add_contact("Анна", "222")
    assert contact.contact_id == 4
    assert contact.created_at == contact.updated_at == now


def test_add_empty_contact_fields_raise_validation_error() -> None:
    # Классы эквивалентности: отсутствует имя / отсутствует телефон.
    for name, phone in [("   ", "123"), ("Иван", "   ")]:
        with pytest.raises(ValidationError):
            PhoneBook().add_contact(name, phone)


def test_find_contacts_by_name_phone_comment_id_and_general_query() -> None:
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
        assert [contact.name for contact in phonebook.find_contacts(query)] == expected


def test_empty_search_query_raises_validation_error() -> None:
    # Пустая строка и пробелы принадлежат одному невалидному классу.
    query = "   "
    with pytest.raises(ValidationError, match="поиска"):
        PhoneBook().find_contacts(query)


def test_search_cache_is_used_and_cleared_after_mutations() -> None:
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


def test_update_contact_changes_selected_fields_and_update_date() -> None:
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
    for field in ("name", "phone"):
        phonebook = PhoneBook([Contact(1, "Иван", "111")])
        with pytest.raises(ValidationError):
            phonebook.update_contact(1, **{field: "   "})


def test_delete_existing_contact_returns_it() -> None:
    phonebook = PhoneBook([Contact(1, "Иван", "111")])
    deleted = phonebook.delete_contact(1)
    assert deleted.name == "Иван"
    assert phonebook.contacts == ()


def test_missing_or_invalid_id_raises_contact_not_found() -> None:
    # Границы допустимого диапазона и отсутствующий положительный ID.
    for contact_id in (0, 999):
        with pytest.raises(ContactNotFoundError):
            PhoneBook().delete_contact(contact_id)


def test_non_integer_id_raises_validation_error() -> None:
    with pytest.raises(ValidationError, match="целым"):
        PhoneBook().get_by_id("abc")  # type: ignore[arg-type]


def test_grouping_sorts_contacts_by_first_letter() -> None:
    phonebook = PhoneBook(
        [Contact(1, "Ирина", "1"), Contact(2, "Анна", "2"), Contact(3, "Иван", "3")]
    )
    groups = phonebook.group_by_first_letter()
    assert list(groups) == ["А", "И"]
    assert [item.name for item in groups["И"]] == ["Иван", "Ирина"]


def test_replace_all_rejects_duplicate_ids() -> None:
    phonebook = PhoneBook()
    with pytest.raises(InvalidDataFormatError, match="повторяющиеся"):
        phonebook.replace_all([Contact(1, "Иван", "1"), Contact(1, "Анна", "2")])


def test_contact_rejects_invalid_id() -> None:
    # Анализ границ: 0 — ближайшее значение ниже минимального ID 1;
    # "abc" — представитель класса значений неверного типа.
    for bad_id in (0, "abc"):
        with pytest.raises(ValidationError):
            Contact(bad_id, "Иван", "111")  # type: ignore[arg-type]


def test_contact_rejects_invalid_dates() -> None:
    for field in ("created_at", "updated_at"):
        with pytest.raises(ValidationError, match="Дата"):
            Contact(1, "Иван", "111", **{field: "2026-01-01"})  # type: ignore[arg-type]


def test_contact_serialization_round_trip() -> None:
    contact = Contact(1, "Иван", "111", "друг", datetime(2026, 1, 1), datetime(2026, 2, 2))
    assert Contact.from_dict(contact.to_dict()) == contact


def test_contact_from_dict_rejects_invalid_data() -> None:
    invalid_equivalence_classes = [
        None,
        {"phone": "111"},
        {"id": 1, "name": "Иван"},
        {"id": "bad", "name": "Иван", "phone": "111"},
        {"id": 1, "name": "", "phone": "111"},
        {"id": 1, "name": "Иван", "phone": "111", "created_at": 123},
        {"id": 1, "name": "Иван", "phone": "111", "updated_at": "not-a-date"},
    ]
    for data in invalid_equivalence_classes:
        with pytest.raises(InvalidDataFormatError):
            Contact.from_dict(data)


def test_reader_handles_missing_and_legacy_files(tmp_path: Path) -> None:
    assert FileReader(tmp_path / "missing.json").read() == []

    path = tmp_path / "legacy.json"
    path.write_text(json.dumps([{"id": 1, "name": "Иван", "phone": "111"}]), encoding="utf-8")
    contact = FileReader(path).read()[0]
    assert isinstance(contact.created_at, datetime)
    assert contact.updated_at == contact.created_at


def test_write_and_open_file_preserve_all_fields(tmp_path: Path) -> None:
    path = tmp_path / "contacts.json"
    contacts = [Contact(1, "Иван", "+7999", "друг", datetime(2026, 1, 1), datetime(2026, 2, 2))]
    FileWriter(path).write(contacts)
    assert FileReader(path).read() == contacts
    assert "Иван" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("content", ["{bad json", '{"id": 1}'])
def test_reader_rejects_invalid_file_content(tmp_path: Path, content: str) -> None:
    path = tmp_path / "contacts.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(InvalidDataFormatError):
        FileReader(path).read()


def test_file_io_errors_are_wrapped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "contacts.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(FileReadError, match="boom"):
        FileReader(path).read()
    with pytest.raises(FileWriteError, match="boom"):
        FileWriter(tmp_path / "contacts.json").write([])


def test_generator_is_reproducible_and_generates_valid_values() -> None:
    first = ContactGenerator(seed=42)
    second = ContactGenerator(seed=42)
    assert first.generate_phone() == second.generate_phone()
    assert first.generate_confirmation_code(8) == second.generate_confirmation_code(8)
    contacts = ContactGenerator(seed=1).generate_contacts(3, start_id=10)
    assert [contact.contact_id for contact in contacts] == [10, 11, 12]


def test_generator_rejects_invalid_code_length() -> None:
    # Ноль — граничное значение непосредственно перед допустимой длиной 1.
    length = 0
    with pytest.raises(ValueError, match="Длина"):
        ContactGenerator().generate_confirmation_code(length)


def test_generator_rejects_negative_count_and_accepts_zero() -> None:
    assert ContactGenerator().generate_contacts(0) == []
    with pytest.raises(ValueError, match="Количество"):
        ContactGenerator().generate_contacts(-1)


def test_controller_crud_and_file_actions(tmp_path: Path) -> None:
    controller, view = make_controller(
        tmp_path,
        ["Иван", "111", "друг", "иван", "1", "Пётр", "222", "", "1", "да"],
    )
    controller.create_contact()
    assert controller.has_changes
    controller.find_contact()
    assert view.shown_contacts[-1][0].name == "Иван"
    controller.update_contact()
    assert controller.phonebook.get_by_id(1).name == "Пётр"
    controller.save_file()
    assert not controller.has_changes
    controller.delete_contact()
    assert controller.phonebook.contacts == ()
    controller.open_file()
    assert controller.phonebook.get_by_id(1).name == "Пётр"


def test_controller_show_actions_and_generate(tmp_path: Path) -> None:
    controller, view = make_controller(tmp_path, ["2"])
    controller.phonebook.add_contact("Иван", "111")
    controller.show_contacts()
    controller.show_grouped_contacts()
    controller.generate_test_contacts()
    assert len(view.shown_contacts) == len(view.shown_groups) == 1
    assert len(controller.phonebook.contacts) == 3
    assert controller.has_changes


def test_controller_rejects_invalid_generation_count(tmp_path: Path) -> None:
    # Таблица решений: неверный тип и нижняя граница диапазона.
    for value in ("abc", "0"):
        controller, _ = make_controller(tmp_path, [value])
        with pytest.raises(ValidationError):
            controller.generate_test_contacts()


def test_controller_rejects_invalid_contact_id(tmp_path: Path) -> None:
    controller, _ = make_controller(tmp_path, ["abc"])
    with pytest.raises(ValidationError, match="ID"):
        controller.delete_contact()


def test_open_file_can_be_cancelled_when_there_are_changes(tmp_path: Path) -> None:
    controller, view = make_controller(tmp_path, ["н"])
    controller.phonebook.add_contact("Локальный", "111")
    controller.has_changes = True
    controller.open_file()
    assert controller.phonebook.contacts[0].name == "Локальный"
    assert view.messages == []


def test_exit_can_save_changes_or_be_cancelled_on_write_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    controller, view = make_controller(tmp_path, ["да"])
    controller.has_changes = True
    controller._is_running = True
    controller.exit_app()
    assert not controller._is_running
    assert "Выход." in view.messages

    controller, view = make_controller(tmp_path, ["да"])
    controller.has_changes = True
    controller._is_running = True
    monkeypatch.setattr(controller.writer, "write", lambda contacts: (_ for _ in ()).throw(FileWriteError("нет доступа")))
    controller.exit_app()
    assert controller._is_running
    assert view.errors == ["нет доступа"]


def test_run_dispatches_actions_handles_errors_and_unknown_menu(tmp_path: Path) -> None:
    controller, view = make_controller(tmp_path, ["unknown", "5", "", "10"])
    controller.run()
    assert "Нет такого пункта меню." in view.errors
    assert any("поиска" in error for error in view.errors)
    assert not controller._is_running


def test_console_view_input_output_and_formatting(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    answers = iter(["  текст  ", "ДА"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    view = ConsoleView()
    view.show_menu()
    assert view.read("prompt") == "текст"
    assert view.confirm("точно?")
    view.show_error("ошибка")
    view.show_contacts([])
    contact = Contact(1, "Иван", "111", created_at=datetime(2026, 1, 2, 3, 4, 5))
    view.show_contacts([contact])
    view.show_grouped_contacts({})
    view.show_grouped_contacts({"И": (contact,)})
    output = capsys.readouterr().out
    assert "Телефонный справочник" in output
    assert "Ошибка: ошибка" in output
    assert "Контакты не найдены." in output
    assert "02.01.2026 03:04:05" in output


def test_main_builds_controller_with_and_without_read_error(monkeypatch: pytest.MonkeyPatch) -> None:
    messages: list[str] = []

    monkeypatch.setattr(application.FileReader, "read", lambda self: (_ for _ in ()).throw(FileReadError("bad")))
    monkeypatch.setattr(application.ConsoleView, "show_error", lambda self, message: messages.append(message))
    monkeypatch.setattr(application.PhoneBookController, "run", lambda self: messages.append("run"))
    application.main()
    assert messages == ["bad", "run"]

    monkeypatch.setattr(application.FileReader, "read", lambda self: [Contact(1, "Иван", "111")])
    monkeypatch.setattr(application.PhoneBookController, "run", lambda self: messages.append(self.phonebook.contacts[0].name))
    application.main()
    assert messages[-1] == "Иван"
