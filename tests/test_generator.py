"""Тесты генератора воспроизводимых тестовых данных."""

import pytest

from generator import ContactGenerator


def test_generator_is_reproducible_and_generates_valid_values() -> None:
    """Одинаковый seed даёт одинаковые данные, а start_id задаёт диапазон ID."""

    first = ContactGenerator(seed=42)
    second = ContactGenerator(seed=42)

    assert first.generate_phone() == second.generate_phone()
    assert first.generate_confirmation_code(8) == second.generate_confirmation_code(8)

    contacts = ContactGenerator(seed=1).generate_contacts(3, start_id=10)
    assert [contact.contact_id for contact in contacts] == [10, 11, 12]


def test_generator_rejects_zero_code_length() -> None:
    """Анализ границ: 0 находится непосредственно перед допустимой длиной 1."""

    with pytest.raises(ValueError, match="Длина"):
        ContactGenerator().generate_confirmation_code(0)


def test_generator_handles_count_boundaries() -> None:
    """Границы количества: 0 допустим, -1 должен завершиться ошибкой."""

    generator = ContactGenerator()

    assert generator.generate_contacts(0) == []
    with pytest.raises(ValueError, match="Количество"):
        generator.generate_contacts(-1)
