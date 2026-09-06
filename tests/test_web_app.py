"""Проверки рабочего каркаса FastAPI."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app


def test_pages_are_registered_and_render_templates(tmp_path: Path) -> None:
    application = create_app(data_path=tmp_path / "contacts.json")
    client = TestClient(application)

    index_response = client.get("/")
    about_response = client.get("/about/")

    assert index_response.status_code == 200
    assert "text/html" in index_response.headers["content-type"]
    assert "Телефонный справочник" in index_response.text
    assert about_response.status_code == 200
    assert "text/html" in about_response.headers["content-type"]
    assert "О проекте" in about_response.text


def test_application_loads_contacts_from_configured_file(tmp_path: Path) -> None:
    data_path = tmp_path / "contacts.json"
    data_path.write_text(
        json.dumps(
            [{"id": 1, "name": "Иван", "phone": "+7 999 123-45-67"}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    application = create_app(data_path=data_path)

    assert application.state.phonebook.get_by_id(1).name == "Иван"
    assert application.state.writer.file_path == data_path


def test_openapi_documentation_is_available(tmp_path: Path) -> None:
    client = TestClient(create_app(data_path=tmp_path / "contacts.json"))

    docs_response = client.get("/docs")
    schema_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert schema_response.status_code == 200
    assert schema_response.json()["info"]["title"] == "Телефонный справочник"
