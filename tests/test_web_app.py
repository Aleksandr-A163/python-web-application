"""Проверки рабочего каркаса FastAPI."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from phonebook.web.application import create_app


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


def test_pages_share_bootstrap_navigation(tmp_path: Path) -> None:
    client = TestClient(create_app(data_path=tmp_path / "contacts.json"))

    index_html = client.get("/").text
    about_html = client.get("/about/").text

    for html in (index_html, about_html):
        assert "bootstrap@5.0.2/dist/css/bootstrap.min.css" in html
        assert "bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" in html
        assert '<nav class="navbar navbar-expand-lg' in html
        assert 'href="http://testserver/"' in html
        assert 'href="http://testserver/about/"' in html
        assert "navbar-toggler" in html
        assert "styles.css" in html
        assert "app.js" in html
        assert 'href="http://testserver/static/favicon.svg"' in html

    normalized_html = " ".join(index_html.split())
    assert 'class="nav-link" href="http://testserver/">Главная</a>' in normalized_html
    assert (
        'class="nav-link" href="http://testserver/about/">О проекте</a>'
        in normalized_html
    )


def test_about_page_describes_site_and_developer(tmp_path: Path) -> None:
    client = TestClient(create_app(data_path=tmp_path / "contacts.json"))

    html = client.get("/about/").text

    assert "О сайте" in html
    assert "Разработчик" in html
    assert "Александр" in html
    assert "python-web-application" in html


def test_home_page_exposes_interactive_contact_browser(tmp_path: Path) -> None:
    client = TestClient(create_app(data_path=tmp_path / "contacts.json"))

    html = client.get("/").text
    styles_response = client.get("/static/styles.css")
    contacts_script_response = client.get("/static/contacts.js")
    favicon_response = client.get("/static/favicon.svg")

    assert 'id="contactSearch"' in html
    assert 'id="contactList"' in html
    assert 'id="refreshContacts"' in html
    assert "contacts.js" in html
    assert styles_response.status_code == 200
    assert "text/css" in styles_response.headers["content-type"]
    assert contacts_script_response.status_code == 200
    assert 'fetch("/api/contacts/")' in contacts_script_response.text
    assert favicon_response.status_code == 200
    assert favicon_response.headers["content-type"].startswith("image/svg+xml")


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
