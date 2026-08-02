"""Application entry point."""

from controller import PhoneBookController
from exceptions import PhoneBookError
from model import FileReader, FileWriter, PhoneBook
from view import ConsoleView


def main() -> None:
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


if __name__ == "__main__":
    main()
