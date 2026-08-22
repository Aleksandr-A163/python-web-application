"""Тест сборки приложения в точке входа."""

import pytest

import main as application
from exceptions import FileReadError
from tests.support.factories import make_contact


def test_main_builds_controller_with_and_without_read_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Таблица решений: приложение стартует после успешного чтения и после его ошибки."""

    events: list[str] = []
    monkeypatch.setattr(
        application.FileReader,
        "read",
        lambda self: (_ for _ in ()).throw(FileReadError("bad")),
    )
    monkeypatch.setattr(
        application.ConsoleView,
        "show_error",
        lambda self, message: events.append(message),
    )
    monkeypatch.setattr(
        application.PhoneBookController,
        "run",
        lambda self: events.append("run"),
    )

    application.main()
    assert events == ["bad", "run"]

    monkeypatch.setattr(
        application.FileReader,
        "read",
        lambda self: [make_contact()],
    )
    monkeypatch.setattr(
        application.PhoneBookController,
        "run",
        lambda self: events.append(self.phonebook.contacts[0].name),
    )

    application.main()
    assert events[-1] == "Иван"
