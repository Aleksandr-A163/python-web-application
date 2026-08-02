"""View: all console input and output."""

from collections.abc import Iterable

from model import Contact


class ConsoleView:
    MENU = """
Телефонный справочник
1. Открыть файл
2. Сохранить файл
3. Показать все контакты
4. Создать контакт
5. Найти контакт
6. Изменить контакт
7. Удалить контакт
8. Выход
"""

    def show_menu(self) -> None:
        print(self.MENU)

    def read(self, prompt: str) -> str:
        return input(prompt).strip()

    def show_message(self, message: str) -> None:
        print(message)

    def show_error(self, message: str) -> None:
        print(f"Ошибка: {message}")

    def show_contacts(self, contacts: Iterable[Contact]) -> None:
        contacts = list(contacts)
        if not contacts:
            self.show_message("Контакты не найдены.")
            return
        for contact in contacts:
            print(
                f"ID: {contact.contact_id} | Имя: {contact.name} | "
                f"Телефон: {contact.phone} | Комментарий: {contact.comment}"
            )

    def confirm(self, prompt: str) -> bool:
        return self.read(f"{prompt} (д/н): ").lower() in {"д", "да", "y", "yes"}
