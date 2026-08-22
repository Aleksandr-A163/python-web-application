"""Контрактные тесты чтения и записи JSON-хранилища."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from exceptions import FileReadError, FileWriteError, InvalidDataFormatError
from model import FileReader, FileWriter
from tests.support.factories import make_contact


def test_reader_handles_missing_and_legacy_files(tmp_path: Path) -> None:
    """Таблица решений: отсутствующий файл и валидный файл старого формата."""

    assert FileReader(tmp_path / "missing.json").read() == []

    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps([{"id": 1, "name": "Иван", "phone": "111"}]),
        encoding="utf-8",
    )
    contact = FileReader(path).read()[0]

    assert isinstance(contact.created_at, datetime)
    assert contact.updated_at == contact.created_at


def test_write_then_read_preserves_all_contact_fields(tmp_path: Path) -> None:
    """Интеграционный round-trip проверяет совместный контракт Reader и Writer."""

    path = tmp_path / "contacts.json"
    contacts = [
        make_contact(
            phone="+7999",
            comment="друг",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 2, 2),
        )
    ]

    FileWriter(path).write(contacts)
    loaded = FileReader(path).read()

    assert loaded == contacts
    assert "Иван" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("content", ["{bad json", '{"id": 1}'])
def test_reader_rejects_invalid_file_classes(tmp_path: Path, content: str) -> None:
    """Параметры представляют синтаксически повреждённый JSON и неверный корень."""

    path = tmp_path / "contacts.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(InvalidDataFormatError):
        FileReader(path).read()


def test_file_io_errors_are_wrapped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Низкоуровневый OSError преобразуется в исключения файлового слоя."""

    path = tmp_path / "contacts.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        Path,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("boom")),
    )

    with pytest.raises(FileReadError, match="boom"):
        FileReader(path).read()
    with pytest.raises(FileWriteError, match="boom"):
        FileWriter(path).write([])
