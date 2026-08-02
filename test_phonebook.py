import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from exceptions import ContactNotFoundError, InvalidDataFormatError, ValidationError
from generator import ContactGenerator
from model import Contact, FileReader, FileWriter, PhoneBook


class SequenceClock:
    def __init__(self, *values: datetime) -> None:
        self._values = iter(values)

    def __call__(self) -> datetime:
        return next(self._values)


class PhoneBookTest(unittest.TestCase):
    def test_add_contact_sets_next_id(self):
        phonebook = PhoneBook([Contact(3, "Иван", "+79990000001")])
        contact = phonebook.add_contact("Анна", "+79990000002")
        self.assertEqual(contact.contact_id, 4)

    def test_new_contact_gets_creation_and_update_dates(self):
        now = datetime(2026, 8, 2, 12, 30)
        contact = PhoneBook(clock=lambda: now).add_contact(
            "Иван", "+79990000001"
        )
        self.assertEqual(contact.created_at, now)
        self.assertEqual(contact.updated_at, now)

    def test_update_changes_updated_at_but_preserves_created_at(self):
        created_at = datetime(2026, 8, 2, 12, 30)
        updated_at = created_at + timedelta(hours=1)
        phonebook = PhoneBook(clock=SequenceClock(created_at, updated_at))
        contact = phonebook.add_contact("Иван", "+79990000001")

        phonebook.update_contact(contact.contact_id, phone="+79990000002")

        self.assertEqual(contact.created_at, created_at)
        self.assertEqual(contact.updated_at, updated_at)

    def test_find_contacts_searches_all_fields(self):
        phonebook = PhoneBook()
        phonebook.add_contact("Иван", "+79990000001", "друг")
        phonebook.add_contact("Анна", "+79990000002", "работа")
        result = phonebook.find_contacts("РАБОТА")
        self.assertEqual([contact.name for contact in result], ["Анна"])

    def test_repeated_search_uses_cache(self):
        phonebook = PhoneBook()
        phonebook.add_contact("Иван", "+79990000001")

        phonebook.find_contacts("иван")
        after_first_search = phonebook.search_cache_info()
        phonebook.find_contacts("иван")
        after_second_search = phonebook.search_cache_info()

        self.assertEqual(after_first_search.misses, 1)
        self.assertEqual(after_second_search.hits, 1)

    def test_mutations_clear_search_cache(self):
        phonebook = PhoneBook()
        first = phonebook.add_contact("Иван", "+79990000001")

        phonebook.find_contacts("иван")
        phonebook.add_contact("Анна", "+79990000002")
        self.assertEqual(phonebook.search_cache_info().currsize, 0)

        phonebook.find_contacts("иван")
        phonebook.update_contact(first.contact_id, comment="друг")
        self.assertEqual(phonebook.search_cache_info().currsize, 0)

        phonebook.find_contacts("иван")
        phonebook.delete_contact(first.contact_id)
        self.assertEqual(phonebook.search_cache_info().currsize, 0)

    def test_grouping_sorts_contacts_and_uses_first_letter(self):
        phonebook = PhoneBook()
        phonebook.add_contact("Ирина", "+79990000001")
        phonebook.add_contact("Анна", "+79990000002")
        phonebook.add_contact("Иван", "+79990000003")
        phonebook.add_contact("Андрей", "+79990000004")

        groups = phonebook.group_by_first_letter()

        self.assertEqual(list(groups), ["А", "И"])
        self.assertEqual(
            [contact.name for contact in groups["А"]],
            ["Андрей", "Анна"],
        )
        self.assertEqual(
            [contact.name for contact in groups["И"]],
            ["Иван", "Ирина"],
        )

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            PhoneBook().add_contact("  ", "+79990000001")

    def test_missing_contact_raises_custom_exception(self):
        with self.assertRaises(ContactNotFoundError):
            PhoneBook().delete_contact(100)

    def test_update_and_delete_existing_contact(self):
        phonebook = PhoneBook()
        contact = phonebook.add_contact("Иван", "+79990000001")
        updated = phonebook.update_contact(contact.contact_id, comment="друг")
        deleted = phonebook.delete_contact(contact.contact_id)
        self.assertEqual(updated.comment, "друг")
        self.assertEqual(deleted, contact)
        self.assertEqual(phonebook.contacts, ())


class StorageTest(unittest.TestCase):
    def test_contacts_without_dates_are_loaded(self):
        old_data = [
            {
                "id": 1,
                "name": "Иван",
                "phone": "+79990000001",
                "comment": "друг",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contacts.json"
            path.write_text(json.dumps(old_data), encoding="utf-8")
            contact = FileReader(path).read()[0]

        self.assertIsInstance(contact.created_at, datetime)
        self.assertEqual(contact.updated_at, contact.created_at)

    def test_dates_survive_write_and_read_without_data_loss(self):
        created_at = datetime(2026, 8, 2, 12, 30, 15, 123456)
        updated_at = datetime(2026, 8, 3, 9, 45, 10, 654321)
        contacts = [
            Contact(
                1,
                "Иван",
                "+79990000001",
                "друг",
                created_at,
                updated_at,
            )
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contacts.json"
            FileWriter(path).write(contacts)
            loaded = FileReader(path).read()

        self.assertEqual(loaded, contacts)
        self.assertEqual(loaded[0].created_at, created_at)
        self.assertEqual(loaded[0].updated_at, updated_at)

    def test_reader_rejects_invalid_json_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contacts.json"
            path.write_text(json.dumps({"name": "Иван"}), encoding="utf-8")
            with self.assertRaises(InvalidDataFormatError):
                FileReader(path).read()


class ContactGeneratorTest(unittest.TestCase):
    def test_generator_creates_requested_number_of_valid_contacts(self):
        contacts = ContactGenerator(seed=42).generate_contacts(5)
        self.assertEqual(len(contacts), 5)
        self.assertEqual([contact.contact_id for contact in contacts], [1, 2, 3, 4, 5])
        self.assertTrue(all(contact.name and contact.phone for contact in contacts))

    def test_fixed_seed_is_reproducible(self):
        first = ContactGenerator(seed=42).generate_contacts(3)
        second = ContactGenerator(seed=42).generate_contacts(3)

        fields = lambda contacts: [
            (contact.contact_id, contact.name, contact.phone, contact.comment)
            for contact in contacts
        ]
        self.assertEqual(fields(first), fields(second))


if __name__ == "__main__":
    unittest.main()
