import unittest

from phonebook import PhoneBook


class PhoneBookTest(unittest.TestCase):
    def test_add_contact_sets_next_id(self):
        phonebook = PhoneBook()

        first = phonebook.add_contact("Иван", "+79990000001", "друг")
        second = phonebook.add_contact("Анна", "+79990000002")

        self.assertEqual(first.contact_id, 1)
        self.assertEqual(second.contact_id, 2)

    def test_find_contacts_searches_all_fields(self):
        phonebook = PhoneBook()
        phonebook.add_contact("Иван", "+79990000001", "друг")
        phonebook.add_contact("Анна", "+79990000002", "работа")

        result = phonebook.find_contacts("работа")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Анна")

    def test_update_contact_changes_existing_contact(self):
        phonebook = PhoneBook()
        contact = phonebook.add_contact("Иван", "+79990000001", "друг")

        updated = phonebook.update_contact(contact.contact_id, phone="+79990000003")

        self.assertTrue(updated)
        self.assertEqual(contact.phone, "+79990000003")

    def test_delete_contact_removes_existing_contact(self):
        phonebook = PhoneBook()
        contact = phonebook.add_contact("Иван", "+79990000001", "друг")

        deleted = phonebook.delete_contact(contact.contact_id)

        self.assertTrue(deleted)
        self.assertEqual(phonebook.get_all(), [])


if __name__ == "__main__":
    unittest.main()
