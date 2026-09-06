"""Архитектурные проверки каркаса веб-приложения."""

from fastapi import APIRouter, FastAPI

from api.contacts import router as contacts_router
from api.router import router as api_router
from app import app, create_app
from model import FileWriter, PhoneBook
from web.pages import router as pages_router


def test_web_application_factory_builds_isolated_application() -> None:
    phonebook = PhoneBook()
    writer = FileWriter("test-contacts.json")

    application = create_app(phonebook=phonebook, writer=writer)

    assert isinstance(application, FastAPI)
    assert application is not app
    assert application.state.phonebook is phonebook
    assert application.state.writer is writer


def test_html_and_api_routers_are_separate() -> None:
    assert isinstance(pages_router, APIRouter)
    assert isinstance(api_router, APIRouter)
    assert isinstance(contacts_router, APIRouter)
    assert pages_router is not api_router
    assert api_router.prefix == "/api"
    assert contacts_router.prefix == "/contacts"
    assert pages_router.include_in_schema is False
