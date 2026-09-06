"""API-роутер контактов."""

from copy import deepcopy
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from phonebook.exceptions import ContactNotFoundError, FileWriteError, ValidationError
from phonebook.model import Contact, PhoneBook
from phonebook.web.dependencies import ContactWriter, get_phonebook, get_writer
from phonebook.web.schemas.contacts import ContactCreate, ContactResponse, ContactUpdate


router = APIRouter(prefix="/contacts", tags=["contacts"])

PhoneBookDependency = Annotated[PhoneBook, Depends(get_phonebook)]
WriterDependency = Annotated[ContactWriter, Depends(get_writer)]
ContactId = Annotated[int, Path(gt=0)]
SearchQuery = Annotated[str | None, Query(min_length=1)]


def get_contact_or_404(phonebook: PhoneBook, contact_id: int) -> Contact:
    """Возвращает контакт или преобразует доменную ошибку в HTTP 404."""

    try:
        return phonebook.get_by_id(contact_id)
    except ContactNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


def save_or_rollback(
    phonebook: PhoneBook,
    writer: ContactWriter,
    snapshot: tuple[Contact, ...],
) -> None:
    """Сохраняет справочник и восстанавливает снимок при отказе записи."""

    try:
        writer.write(phonebook.contacts)
    except FileWriteError as error:
        phonebook.replace_all(snapshot)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить изменения.",
        ) from error


@router.get("/", response_model=list[ContactResponse])
def read_contacts(
    phonebook: PhoneBookDependency,
    query: SearchQuery = None,
) -> list[ContactResponse]:
    """Возвращает все контакты или результаты поиска."""

    try:
        contacts = (
            phonebook.contacts if query is None else phonebook.find_contacts(query)
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    return [ContactResponse.from_contact(contact) for contact in contacts]


@router.get("/{contact_id}", response_model=ContactResponse)
def read_contact(
    contact_id: ContactId,
    phonebook: PhoneBookDependency,
) -> ContactResponse:
    """Возвращает контакт по идентификатору."""

    return ContactResponse.from_contact(get_contact_or_404(phonebook, contact_id))


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

    snapshot = deepcopy(phonebook.contacts)
    contact = phonebook.add_contact(
        name=payload.name,
        phone=payload.phone,
        comment=payload.comment,
    )
    save_or_rollback(phonebook, writer, snapshot)
    return ContactResponse.from_contact(contact)


@router.patch("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: ContactId,
    payload: ContactUpdate,
    phonebook: PhoneBookDependency,
    writer: WriterDependency,
) -> ContactResponse:
    """Частично изменяет контакт и сохраняет справочник."""

    get_contact_or_404(phonebook, contact_id)
    snapshot = deepcopy(phonebook.contacts)
    contact = phonebook.update_contact(
        contact_id=contact_id,
        name=payload.name,
        phone=payload.phone,
        comment=payload.comment,
    )
    save_or_rollback(phonebook, writer, snapshot)
    return ContactResponse.from_contact(contact)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_contact(
    contact_id: ContactId,
    phonebook: PhoneBookDependency,
    writer: WriterDependency,
) -> Response:
    """Удаляет контакт и возвращает пустой ответ."""

    get_contact_or_404(phonebook, contact_id)
    snapshot = deepcopy(phonebook.contacts)
    phonebook.delete_contact(contact_id)
    save_or_rollback(phonebook, writer, snapshot)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
