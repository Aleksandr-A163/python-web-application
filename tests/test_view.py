"""Тест консольного адаптера представления."""

from datetime import datetime

import pytest

from tests.support.factories import make_contact
from phonebook.cli.view import ConsoleView


def test_console_view_input_output_and_formatting(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Консольный контракт проверяет ввод, подтверждение, ошибки и формат даты."""

    answers = iter(["  текст  ", "ДА"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    view = ConsoleView()

    view.show_menu()
    assert view.read("prompt") == "текст"
    assert view.confirm("точно?")
    view.show_error("ошибка")
    view.show_contacts([])
    contact = make_contact(created_at=datetime(2026, 1, 2, 3, 4, 5))
    view.show_contacts([contact])
    view.show_grouped_contacts({})
    view.show_grouped_contacts({"И": (contact,)})

    output = capsys.readouterr().out
    assert "Телефонный справочник" in output
    assert "Ошибка: ошибка" in output
    assert "Контакты не найдены." in output
    assert "02.01.2026 03:04:05" in output
