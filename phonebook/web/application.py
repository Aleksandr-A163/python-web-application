"""Сборка FastAPI-приложения."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from phonebook.model import FileReader, FileWriter, PhoneBook
from phonebook.web.api.router import router as api_router
from phonebook.web.dependencies import ContactWriter
from phonebook.web.pages import router as pages_router


STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"


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
    application.mount(
        "/static",
        StaticFiles(directory=STATIC_DIRECTORY),
        name="static",
    )
    application.include_router(pages_router)
    application.include_router(api_router)
    return application


app = create_app()
