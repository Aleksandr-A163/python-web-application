import json
import tempfile
import unittest
from pathlib import Path

from exceptions import ContactNotFoundError, InvalidDataFormatError, ValidationError
from model import Contact, FileReader, FileWriter, PhoneBook


class PhoneBookTest(unittest.TestCase):
    def test_add_contact_sets_next_id(self):
        phonebook = PhoneBook([Contact(3, "Иван", "+79990000001")])
        contact = phonebook.add_contact("Анна", "+79990000002")
        self.assertEqual(contact.contact_id, 4)

    def test_find_contacts_searches_all_fields(self):
        phonebook = PhoneBook()
        phonebook.add_contact("Иван", "+79990000001", "друг")
        phonebook.add_contact("Анна", "+79990000002", "работа")
        result = phonebook.find_contacts("РАБОТА")
        self.assertEqual([contact.name for contact in result], ["Анна"])

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            PhoneBook().add_contact("  ", "+79990000001")

    def test_missing_contact_raises_custom_exception(self):
        with self.assertRaises(ContactNotFoundError):
            PhoneBook().delete_contact(100)

    def test_reader_and_writer_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contacts.json"
            contacts = [Contact(1, "Иван", "+79990000001", "друг")]
            FileWriter(path).write(contacts)
            self.assertEqual(FileReader(path).read(), contacts)

    def test_reader_rejects_invalid_json_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contacts.json"
            path.write_text(json.dumps({"name": "Иван"}), encoding="utf-8")
            with self.assertRaises(InvalidDataFormatError):
                FileReader(path).read()


if __name__ == "__main__":
    unittest.main()
