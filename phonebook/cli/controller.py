"""Контроллер: связывает модель и консольное представление."""

from collections.abc import Callable

from phonebook.cli.view import ConsoleView
from phonebook.exceptions import PhoneBookError, ValidationError
from phonebook.generator import ContactGenerator
from phonebook.model import FileReader, FileWriter, PhoneBook


class PhoneBookController:
    def __init__(
        self,
        phonebook: PhoneBook,
        reader: FileReader,
        writer: FileWriter,
        view: ConsoleView,
        generator: ContactGenerator | None = None,
    ) -> None:
        self.phonebook = phonebook
        self.reader = reader
        self.writer = writer
        self.view = view
        self.generator = generator or ContactGenerator()
        self.has_changes: bool = False
        self._is_running: bool = False

    def run(self) -> None:
        actions: dict[str, Callable[[], None]] = {
            "1": self.open_file,
            "2": self.save_file,
            "3": self.show_contacts,
            "4": self.create_contact,
            "5": self.find_contact,
            "6": self.update_contact,
            "7": self.delete_contact,
            "8": self.show_grouped_contacts,
            "9": self.generate_test_contacts,
        }
        self._is_running = True
        while self._is_running:
            self.view.show_menu()
            choice = self.view.read("Выберите действие: ")
            if choice == "10":
                self.exit_app()
                continue
            action = actions.get(choice)
            if action is None:
                self.view.show_error("Нет такого пункта меню.")
                continue
            try:
                action()
            except PhoneBookError as error:
                self.view.show_error(str(error))

    def open_file(self) -> None:
        if self.has_changes and not self.view.confirm(
            "Есть несохранённые изменения. Открыть файл без сохранения?"
        ):
            return
        self.phonebook.replace_all(self.reader.read())
        self.has_changes = False
        self.view.show_message("Файл открыт.")

    def save_file(self) -> None:
        self.writer.write(self.phonebook.contacts)
        self.has_changes = False
        self.view.show_message("Файл сохранён.")

    def show_contacts(self) -> None:
        self.view.show_contacts(self.phonebook.contacts)

    def create_contact(self) -> None:
        contact = self.phonebook.add_contact(
            self.view.read("Введите имя: "),
            self.view.read("Введите телефон: "),
            self.view.read("Введите комментарий: "),
        )
        self.has_changes = True
        self.view.show_message(f"Контакт создан. ID: {contact.contact_id}")

    def find_contact(self) -> None:
        query = self.view.read("Введите текст для поиска: ")
        self.view.show_contacts(self.phonebook.find_contacts(query))

    def update_contact(self) -> None:
        contact_id = self._read_contact_id()
        contact = self.phonebook.get_by_id(contact_id)
        self.view.show_message("Оставьте поле пустым, чтобы не менять его.")
        name = self.view.read(f"Новое имя ({contact.name}): ")
        phone = self.view.read(f"Новый телефон ({contact.phone}): ")
        comment = self.view.read(f"Новый комментарий ({contact.comment}): ")
        self.phonebook.update_contact(
            contact_id,
            name=name or None,
            phone=phone or None,
            comment=comment or None,
        )
        self.has_changes = True
        self.view.show_message("Контакт изменён.")

    def delete_contact(self) -> None:
        contact = self.phonebook.delete_contact(self._read_contact_id())
        self.has_changes = True
        self.view.show_message(f"Контакт «{contact.name}» удалён.")

    def show_grouped_contacts(self) -> None:
        self.view.show_grouped_contacts(self.phonebook.group_by_first_letter())

    def generate_test_contacts(self) -> None:
        value = self.view.read("Введите количество тестовых контактов: ")
        try:
            count = int(value)
        except ValueError as error:
            raise ValidationError(
                "Количество контактов должно быть целым числом."
            ) from error
        if count < 1:
            raise ValidationError(
                "Количество контактов должно быть положительным числом."
            )

        generated = self.generator.generate_contacts(count)
        for contact in generated:
            self.phonebook.add_contact(
                contact.name,
                contact.phone,
                contact.comment,
            )
        self.has_changes = True
        self.view.show_message(f"Создано тестовых контактов: {count}.")

    def exit_app(self) -> None:
        if self.has_changes and self.view.confirm(
            "Есть несохранённые изменения. Сохранить?"
        ):
            try:
                self.save_file()
            except PhoneBookError as error:
                self.view.show_error(str(error))
                return
        self.view.show_message("Выход.")
        self._is_running = False

    def _read_contact_id(self) -> int:
        value = self.view.read("Введите ID контакта: ")
        try:
            return int(value)
        except ValueError as error:
            raise ValidationError("ID контакта должен быть целым числом.") from error
