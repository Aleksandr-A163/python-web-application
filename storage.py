import json
from pathlib import Path

from contacts import Contact


class ContactStorage:
    def __init__(self, file_path: str = "contacts.json") -> None:
        self.file_path = Path(file_path)

    def load(self) -> list[Contact]:
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print("Файл поврежден или содержит неверный JSON. Загружен пустой справочник.")
            return []

        if not isinstance(data, list):
            print("Файл должен содержать список контактов. Загружен пустой справочник.")
            return []

        contacts = []
        for item in data:
            try:
                contacts.append(Contact.from_dict(item))
            except (KeyError, TypeError, ValueError):
                print("Один контакт в файле пропущен из-за неверной структуры.")

        return contacts

    def save(self, contacts: list[Contact]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(
                [contact.to_dict() for contact in contacts],
                file,
                ensure_ascii=False,
                indent=2,
            )
