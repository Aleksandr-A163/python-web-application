"""Pydantic-схемы HTTP-контрактов контактов."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from phonebook.model import Contact


class ContactCreate(BaseModel):
    """Данные, которые клиент передаёт для создания контакта."""

    name: str
    phone: str
    comment: str = ""

    @field_validator("name", "phone", "comment")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        """Удаляет внешние пробелы у текстовых полей."""

        return value.strip()

    @field_validator("name", "phone")
    @classmethod
    def reject_blank_required_fields(cls, value: str) -> str:
        """Не допускает пустые обязательные поля."""

        if not value:
            raise ValueError("Поле не должно быть пустым.")
        return value


class ContactResponse(BaseModel):
    """Публичное представление контакта."""

    id: int = Field(gt=0)
    name: str
    phone: str
    comment: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_contact(cls, contact: Contact) -> "ContactResponse":
        """Создаёт HTTP-схему из доменной сущности."""

        return cls(
            id=contact.contact_id,
            name=contact.name,
            phone=contact.phone,
            comment=contact.comment,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )
