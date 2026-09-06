"""Поведенческие тесты сценариев PhoneBookController."""

import pytest

from phonebook.exceptions import FileWriteError, ValidationError
from tests.support.factories import ControllerFactory


def test_controller_runs_complete_crud_workflow(
    controller_factory: ControllerFactory,
) -> None:
    """State Transition: create → find → update → save → delete → open."""

    controller, view = controller_factory(
        ["Иван", "111", "друг", "иван", "1", "Пётр", "222", "", "1", "да"]
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


def test_controller_shows_and_generates_contacts(
    controller_factory: ControllerFactory,
) -> None:
    """Команды просмотра и генерации делегируются нужным компонентам."""

    controller, view = controller_factory(["2"])
    controller.phonebook.add_contact("Иван", "111")

    controller.show_contacts()
    controller.show_grouped_contacts()
    controller.generate_test_contacts()

    assert len(view.shown_contacts) == len(view.shown_groups) == 1
    assert len(controller.phonebook.contacts) == 3
    assert controller.has_changes


def test_controller_rejects_invalid_generation_count(
    controller_factory: ControllerFactory,
) -> None:
    """Таблица решений: неверный тип и нижняя недопустимая граница количества."""

    for value in ("abc", "0"):
        controller, _ = controller_factory([value])
        with pytest.raises(ValidationError):
            controller.generate_test_contacts()


def test_controller_rejects_non_integer_contact_id(
    controller_factory: ControllerFactory,
) -> None:
    """Контроллер преобразует нечисловой ввод ID в ValidationError."""

    controller, _ = controller_factory(["abc"])

    with pytest.raises(ValidationError, match="ID"):
        controller.delete_contact()


def test_open_file_can_be_cancelled_with_unsaved_changes(
    controller_factory: ControllerFactory,
) -> None:
    """Отрицательное подтверждение сохраняет текущее состояние справочника."""

    controller, view = controller_factory(["н"])
    controller.phonebook.add_contact("Локальный", "111")
    controller.has_changes = True

    controller.open_file()

    assert controller.phonebook.contacts[0].name == "Локальный"
    assert view.messages == []


def test_exit_handles_successful_and_failed_save(
    controller_factory: ControllerFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Таблица решений: успешное сохранение завершает работу, ошибка — отменяет выход."""

    controller, view = controller_factory(["да"])
    controller.has_changes = True
    controller._is_running = True
    controller.exit_app()
    assert not controller._is_running
    assert "Выход." in view.messages

    controller, view = controller_factory(["да"])
    controller.has_changes = True
    controller._is_running = True
    monkeypatch.setattr(
        controller.writer,
        "write",
        lambda contacts: (_ for _ in ()).throw(FileWriteError("нет доступа")),
    )

    controller.exit_app()

    assert controller._is_running
    assert view.errors == ["нет доступа"]


def test_run_dispatches_menu_and_handles_expected_errors(
    controller_factory: ControllerFactory,
) -> None:
    """Главный цикл обрабатывает неизвестную команду, доменную ошибку и выход."""

    controller, view = controller_factory(["unknown", "5", "", "10"])

    controller.run()

    assert "Нет такого пункта меню." in view.errors
    assert any("поиска" in error for error in view.errors)
    assert not controller._is_running
