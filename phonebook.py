from contacts import Contact


class PhoneBook:
    def __init__(self, contacts: list[Contact] | None = None) -> None:
        self.contacts = contacts or []

    def get_all(self) -> list[Contact]:
        return self.contacts

    def add_contact(self, name: str, phone: str, comment: str = "") -> Contact:
        contact = Contact(
            contact_id=self._get_next_id(),
            name=name.strip(),
            phone=phone.strip(),
            comment=comment.strip(),
        )
        self.contacts.append(contact)
        return contact

    def find_contacts(self, query: str) -> list[Contact]:
        query = query.strip().lower()
        if not query:
            return []

        result = []
        for contact in self.contacts:
            fields = [
                str(contact.contact_id),
                contact.name,
                contact.phone,
                contact.comment,
            ]
            if any(query in field.lower() for field in fields):
                result.append(contact)

        return result

    def get_by_id(self, contact_id: int) -> Contact | None:
        for contact in self.contacts:
            if contact.contact_id == contact_id:
                return contact
        return None

    def update_contact(
        self,
        contact_id: int,
        name: str | None = None,
        phone: str | None = None,
        comment: str | None = None,
    ) -> bool:
        contact = self.get_by_id(contact_id)
        if contact is None:
            return False

        if name is not None and name.strip():
            contact.name = name.strip()
        if phone is not None and phone.strip():
            contact.phone = phone.strip()
        if comment is not None:
            contact.comment = comment.strip()

        return True

    def delete_contact(self, contact_id: int) -> bool:
        contact = self.get_by_id(contact_id)
        if contact is None:
            return False

        self.contacts.remove(contact)
        return True

    def _get_next_id(self) -> int:
        if not self.contacts:
            return 1
        return max(contact.contact_id for contact in self.contacts) + 1
