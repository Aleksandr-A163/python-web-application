from console_app import ConsoleApp
from phonebook import PhoneBook
from storage import ContactStorage


def main() -> None:
    storage = ContactStorage("contacts.json")
    phonebook = PhoneBook(storage.load())
    app = ConsoleApp(storage, phonebook)
    app.run()


if __name__ == "__main__":
    main()
