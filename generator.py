"""Генерация тестовых контактов и кодов подтверждения."""

import random

from model import Contact


class ContactGenerator:
    """Создаёт воспроизводимые случайные тестовые данные."""

    NAMES: tuple[str, ...] = (
        "Александр",
        "Анна",
        "Виктор",
        "Елена",
        "Иван",
        "Мария",
        "Николай",
        "Ольга",
    )
    COMMENTS: tuple[str, ...] = (
        "друг",
        "работа",
        "семья",
        "учёба",
        "тестовый контакт",
    )

    def __init__(self, seed: int | None = None) -> None:
        self._random: random.Random = random.Random(seed)

    def generate_phone(self) -> str:
        return "+79" + "".join(
            str(self._random.randint(0, 9)) for _ in range(9)
        )

    def generate_confirmation_code(self, length: int = 6) -> str:
        if length < 1:
            raise ValueError("Длина кода должна быть положительным числом.")
        return "".join(str(self._random.randint(0, 9)) for _ in range(length))

    def generate_contact(self, contact_id: int = 1) -> Contact:
        return Contact(
            contact_id=contact_id,
            name=self._random.choice(self.NAMES),
            phone=self.generate_phone(),
            comment=self._random.choice(self.COMMENTS),
        )

    def generate_contacts(
        self,
        count: int,
        start_id: int = 1,
    ) -> list[Contact]:
        if count < 0:
            raise ValueError("Количество контактов не может быть отрицательным.")
        return [
            self.generate_contact(start_id + offset)
            for offset in range(count)
        ]
