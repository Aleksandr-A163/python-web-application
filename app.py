"""Точка сборки веб-приложения."""

from pathlib import Path

from fastapi import FastAPI

from api.router import router as api_router
from model import FileReader, FileWriter, PhoneBook
from web.dependencies import ContactWriter
from web.pages import router as pages_router


def create_app(
    phonebook: PhoneBook | None = None,
    writer: ContactWriter | None = None,
    data_path: str | Path = "contacts.json",
) -> FastAPI:
    """Создаёт изолированный экземпляр FastAPI-приложения."""

    application = FastAPI(title="Телефонный справочник")
    application.state.phonebook = (
        phonebook if phonebook is not None else PhoneBook(FileReader(data_path).read())
    )
    application.state.writer = (
        writer if writer is not None else FileWriter(data_path)
    )
    application.include_router(pages_router)
    application.include_router(api_router)
    return application


app = create_app()
