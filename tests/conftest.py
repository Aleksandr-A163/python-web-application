"""Общие pytest-фикстуры, доступные всем тестовым модулям."""

from __future__ import annotations

from pathlib import Path

import pytest

from phonebook.cli.controller import PhoneBookController
from phonebook.model import PhoneBook
from tests.support.doubles import StubView
from tests.support.factories import ControllerFactory, make_controller


@pytest.fixture
def controller_factory(tmp_path: Path) -> ControllerFactory:
    """Предоставляет Factory Method для контроллеров с временным JSON-файлом."""

    def factory(
        inputs: list[str] | None = None,
        phonebook: PhoneBook | None = None,
    ) -> tuple[PhoneBookController, StubView]:
        return make_controller(tmp_path, inputs, phonebook)

    return factory
