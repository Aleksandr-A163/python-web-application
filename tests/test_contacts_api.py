"""Контрактные тесты JSON API контактов."""

import json
from collections.abc import Iterable
from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app
from exceptions import FileWriteError
from model import Contact, PhoneBook


def make_client(tmp_path: Path, phonebook: PhoneBook | None = None) -> TestClient:
    return TestClient(
        create_app(
            phonebook=phonebook if phonebook is not None else PhoneBook(),
            data_path=tmp_path / "contacts.json",
        )
    )


def test_read_contacts_returns_empty_and_filled_lists(tmp_path: Path) -> None:
    empty_client = make_client(tmp_path)
    filled_client = make_client(
        tmp_path,
        PhoneBook([Contact(1, "Иван", "+7 999 123-45-67", "Коллега")]),
    )

    assert empty_client.get("/api/contacts/").json() == []

    response = filled_client.get("/api/contacts/")

    assert response.status_code == 200
    assert response.json()[0]["id"] == 1
    assert response.json()[0]["name"] == "Иван"
    assert response.json()[0]["comment"] == "Коллега"
    assert "created_at" in response.json()[0]
    assert "updated_at" in response.json()[0]


def test_read_contact_returns_entity_or_not_found(tmp_path: Path) -> None:
    client = make_client(
        tmp_path,
        PhoneBook([Contact(1, "Иван", "+7 999 123-45-67")]),
    )

    response = client.get("/api/contacts/1")
    missing_response = client.get("/api/contacts/999")

    assert response.status_code == 200
    assert response.json()["name"] == "Иван"
    assert missing_response.status_code == 404
    assert missing_response.json() == {
        "detail": "Контакт с ID 999 не найден."
    }


def test_read_contact_rejects_invalid_id(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    assert client.get("/api/contacts/0").status_code == 422
    assert client.get("/api/contacts/not-a-number").status_code == 422


def test_create_contact_returns_and_persists_entity(tmp_path: Path) -> None:
    data_path = tmp_path / "contacts.json"
    client = TestClient(create_app(phonebook=PhoneBook(), data_path=data_path))

    response = client.post(
        "/api/contacts/",
        json={
            "name": "  Иван Иванов  ",
            "phone": "  +7 999 123-45-67  ",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Иван Иванов"
    assert response.json()["phone"] == "+7 999 123-45-67"
    assert response.json()["comment"] == ""
    assert client.get("/api/contacts/1").json() == response.json()
    assert json.loads(data_path.read_text(encoding="utf-8"))[0]["id"] == 1


def test_create_contact_rejects_invalid_payload(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    assert client.post(
        "/api/contacts/",
        json={"name": "   ", "phone": "+7 999 123-45-67"},
    ).status_code == 422
    assert client.post(
        "/api/contacts/",
        json={"name": "Иван", "phone": "   "},
    ).status_code == 422
    assert client.post(
        "/api/contacts/",
        json={"name": "Иван"},
    ).status_code == 422


class FailingWriter:
    """Имитирует отказ хранилища без раскрытия системных деталей."""

    def write(self, contacts: Iterable[Contact]) -> None:
        raise FileWriteError("Секретный путь к файлу")


def test_create_contact_rolls_back_after_write_error(tmp_path: Path) -> None:
    phonebook = PhoneBook()
    application = create_app(
        phonebook=phonebook,
        writer=FailingWriter(),
        data_path=tmp_path / "contacts.json",
    )
    client = TestClient(application)

    response = client.post(
        "/api/contacts/",
        json={"name": "Иван", "phone": "+7 999 123-45-67"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Не удалось сохранить контакт."}
    assert phonebook.contacts == ()
    assert "Секретный" not in response.text


def test_contacts_api_is_in_openapi_schema(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    paths = client.get("/openapi.json").json()["paths"]

    assert set(paths["/api/contacts/"]) == {"get", "post"}
    assert set(paths["/api/contacts/{contact_id}"]) == {"get"}
