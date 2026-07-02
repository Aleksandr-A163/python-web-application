from phonebook import PhoneBook
from storage import ContactStorage


class ConsoleApp:
    def __init__(self, storage: ContactStorage, phonebook: PhoneBook) -> None:
        self.storage = storage
        self.phonebook = phonebook
        self.has_changes = False

    def run(self) -> None:
        while True:
            self._show_menu()
            choice = input("Выберите действие: ").strip()

            if choice == "1":
                self.open_file()
            elif choice == "2":
                self.save_file()
            elif choice == "3":
                self.show_contacts()
            elif choice == "4":
                self.create_contact()
            elif choice == "5":
                self.find_contact()
            elif choice == "6":
                self.update_contact()
            elif choice == "7":
                self.delete_contact()
            elif choice == "8":
                if self.exit_app():
                    break
            else:
                print("Нет такого пункта меню.")

    def open_file(self) -> None:
        if self.has_changes:
            answer = input("Есть несохраненные изменения. Открыть файл без сохранения? (д/н): ")
            if answer.strip().lower() not in ("д", "y", "yes"):
                return

        self.phonebook.contacts = self.storage.load()
        self.has_changes = False
        print("Файл открыт.")

    def save_file(self) -> None:
        self.storage.save(self.phonebook.get_all())
        self.has_changes = False
        print("Файл сохранен.")

    def show_contacts(self) -> None:
        self._print_contacts(self.phonebook.get_all())

    def create_contact(self) -> None:
        name = self._read_required("Введите имя: ")
        phone = self._read_required("Введите телефон: ")
        comment = input("Введите комментарий: ").strip()

        contact = self.phonebook.add_contact(name, phone, comment)
        self.has_changes = True
        print(f"Контакт создан. ID: {contact.contact_id}")

    def find_contact(self) -> None:
        query = input("Введите текст для поиска: ").strip()
        contacts = self.phonebook.find_contacts(query)
        self._print_contacts(contacts)

    def update_contact(self) -> None:
        contact_id = self._read_contact_id()
        if contact_id is None:
            return

        contact = self.phonebook.get_by_id(contact_id)
        if contact is None:
            print("Контакт с таким ID не найден.")
            return

        print("Оставьте поле пустым, если его не нужно менять.")
        name = input(f"Новое имя ({contact.name}): ")
        phone = input(f"Новый телефон ({contact.phone}): ")
        comment = input(f"Новый комментарий ({contact.comment}): ")

        self.phonebook.update_contact(
            contact_id,
            name=name or None,
            phone=phone or None,
            comment=comment or None,
        )
        self.has_changes = True
        print("Контакт изменен.")

    def delete_contact(self) -> None:
        contact_id = self._read_contact_id()
        if contact_id is None:
            return

        if self.phonebook.delete_contact(contact_id):
            self.has_changes = True
            print("Контакт удален.")
        else:
            print("Контакт с таким ID не найден.")

    def exit_app(self) -> bool:
        if self.has_changes:
            answer = input("Есть несохраненные изменения. Сохранить? (д/н): ").strip().lower()
            if answer in ("д", "y", "yes"):
                self.save_file()
        print("Выход.")
        return True

    def _show_menu(self) -> None:
        print()
        print("Телефонный справочник")
        print("1. Открыть файл")
        print("2. Сохранить файл")
        print("3. Показать все контакты")
        print("4. Создать контакт")
        print("5. Найти контакт")
        print("6. Изменить контакт")
        print("7. Удалить контакт")
        print("8. Выход")

    def _print_contacts(self, contacts) -> None:
        if not contacts:
            print("Контакты не найдены.")
            return

        for contact in contacts:
            print(
                f"ID: {contact.contact_id} | "
                f"Имя: {contact.name} | "
                f"Телефон: {contact.phone} | "
                f"Комментарий: {contact.comment}"
            )

    def _read_required(self, prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("Поле не должно быть пустым.")

    def _read_contact_id(self) -> int | None:
        value = input("Введите ID контакта: ").strip()
        try:
            return int(value)
        except ValueError:
            print("ID должен быть числом.")
            return None
