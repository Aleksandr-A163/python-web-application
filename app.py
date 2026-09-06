"""Точка сборки веб-приложения."""

from fastapi import FastAPI

from api.router import router as api_router
from model import FileWriter, PhoneBook
from web.pages import router as pages_router


def create_app(
    phonebook: PhoneBook | None = None,
    writer: FileWriter | None = None,
) -> FastAPI:
    """Создаёт изолированный экземпляр FastAPI-приложения."""

    application = FastAPI(title="Телефонный справочник")
    application.state.phonebook = phonebook or PhoneBook()
    application.state.writer = writer or FileWriter("contacts.json")
    application.include_router(pages_router)
    application.include_router(api_router)
    return application


app = create_app()
