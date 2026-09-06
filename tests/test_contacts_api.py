"""Контрактные тесты JSON API контактов."""

import json
from collections.abc import Iterable
from pathlib import Path

from fastapi.testclient import TestClient

from phonebook.exceptions import FileWriteError
from phonebook.model import Contact, PhoneBook
from phonebook.web.application import create_app


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


def test_read_contacts_supports_search(tmp_path: Path) -> None:
    client = make_client(
        tmp_path,
        PhoneBook(
            [
                Contact(1, "Иван", "+7 999 111-11-11", "Коллега"),
                Contact(2, "Анна", "+7 999 222-22-22", "Семья"),
            ]
        ),
    )

    response = client.get("/api/contacts/", params={"query": "СЕМЬЯ"})
    blank_response = client.get("/api/contacts/", params={"query": "   "})

    assert response.status_code == 200
    assert [contact["name"] for contact in response.json()] == ["Анна"]
    assert blank_response.status_code == 422


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


def test_update_contact_changes_selected_fields_and_persists(tmp_path: Path) -> None:
    data_path = tmp_path / "contacts.json"
    phonebook = PhoneBook([Contact(1, "Иван", "+7 999 123-45-67", "Коллега")])
    client = TestClient(create_app(phonebook=phonebook, data_path=data_path))

    response = client.patch(
        "/api/contacts/1",
        json={"phone": "  +7 900 555-12-34  ", "comment": "  Новый номер  "},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Иван"
    assert response.json()["phone"] == "+7 900 555-12-34"
    assert response.json()["comment"] == "Новый номер"
    persisted = json.loads(data_path.read_text(encoding="utf-8"))[0]
    assert persisted["phone"] == "+7 900 555-12-34"


def test_update_contact_validates_payload_and_id(tmp_path: Path) -> None:
    client = make_client(
        tmp_path,
        PhoneBook([Contact(1, "Иван", "+7 999 123-45-67")]),
    )

    assert client.patch("/api/contacts/1", json={}).status_code == 422
    assert client.patch("/api/contacts/1", json={"name": "   "}).status_code == 422
    assert client.patch("/api/contacts/999", json={"name": "Анна"}).status_code == 404


def test_delete_contact_removes_and_persists_entity(tmp_path: Path) -> None:
    data_path = tmp_path / "contacts.json"
    phonebook = PhoneBook(
        [
            Contact(1, "Иван", "+7 999 111-11-11"),
            Contact(2, "Анна", "+7 999 222-22-22"),
        ]
    )
    client = TestClient(create_app(phonebook=phonebook, data_path=data_path))

    response = client.delete("/api/contacts/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/api/contacts/1").status_code == 404
    assert [item["id"] for item in json.loads(data_path.read_text("utf-8"))] == [2]
    assert client.delete("/api/contacts/999").status_code == 404


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
    assert response.json() == {"detail": "Не удалось сохранить изменения."}
    assert phonebook.contacts == ()
    assert "Секретный" not in response.text


def test_update_and_delete_roll_back_after_write_error(tmp_path: Path) -> None:
    original = Contact(1, "Иван", "+7 999 123-45-67", "Исходный")
    phonebook = PhoneBook([original])
    client = TestClient(
        create_app(
            phonebook=phonebook,
            writer=FailingWriter(),
            data_path=tmp_path / "contacts.json",
        )
    )

    update_response = client.patch(
        "/api/contacts/1",
        json={"name": "Изменённый"},
    )
    delete_response = client.delete("/api/contacts/1")

    assert update_response.status_code == 500
    assert phonebook.get_by_id(1).name == "Иван"
    assert delete_response.status_code == 500
    assert phonebook.get_by_id(1).name == "Иван"


def test_contacts_api_is_in_openapi_schema(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    paths = client.get("/openapi.json").json()["paths"]

    assert set(paths["/api/contacts/"]) == {"get", "post"}
    assert set(paths["/api/contacts/{contact_id}"]) == {"get", "patch", "delete"}
