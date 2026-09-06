"""Сборка консольного приложения."""

from phonebook.cli.controller import PhoneBookController
from phonebook.cli.view import ConsoleView
from phonebook.exceptions import PhoneBookError
from phonebook.model import FileReader, FileWriter, PhoneBook


def main() -> None:
    """Загружает справочник и запускает консольный контроллер."""

    file_path = "contacts.json"
    view = ConsoleView()
    reader = FileReader(file_path)
    try:
        phonebook = PhoneBook(reader.read())
    except PhoneBookError as error:
        view.show_error(str(error))
        phonebook = PhoneBook()

    controller = PhoneBookController(
        phonebook=phonebook,
        reader=reader,
        writer=FileWriter(file_path),
        view=view,
    )
    controller.run()
