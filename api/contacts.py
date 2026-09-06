"""API-роутер контактов."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from exceptions import ContactNotFoundError, FileWriteError, ValidationError
from model import PhoneBook
from schemas.contacts import ContactCreate, ContactResponse
from web.dependencies import ContactWriter, get_phonebook, get_writer


router = APIRouter(prefix="/contacts", tags=["contacts"])

PhoneBookDependency = Annotated[PhoneBook, Depends(get_phonebook)]
WriterDependency = Annotated[ContactWriter, Depends(get_writer)]
ContactId = Annotated[int, Path(gt=0)]


@router.get("/", response_model=list[ContactResponse])
def read_contacts(phonebook: PhoneBookDependency) -> list[ContactResponse]:
    """Возвращает все контакты в порядке телефонного справочника."""

    return [ContactResponse.from_contact(contact) for contact in phonebook.contacts]


@router.get("/{contact_id}", response_model=ContactResponse)
def read_contact(
    contact_id: ContactId,
    phonebook: PhoneBookDependency,
) -> ContactResponse:
    """Возвращает контакт по идентификатору."""

    try:
        contact = phonebook.get_by_id(contact_id)
    except ContactNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return ContactResponse.from_contact(contact)


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    payload: ContactCreate,
    phonebook: PhoneBookDependency,
    writer: WriterDependency,
) -> ContactResponse:
    """Создаёт контакт и сохраняет актуальное состояние справочника."""

    try:
        contact = phonebook.add_contact(
            name=payload.name,
            phone=payload.phone,
            comment=payload.comment,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    try:
        writer.write(phonebook.contacts)
    except FileWriteError as error:
        phonebook.delete_contact(contact.contact_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить контакт.",
        ) from error

    return ContactResponse.from_contact(contact)
