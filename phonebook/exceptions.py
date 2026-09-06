"""Доменные исключения телефонного справочника."""


class PhoneBookError(Exception):
    """Базовый класс ожидаемых ошибок приложения."""


class ValidationError(PhoneBookError):
    """Ошибка некорректных данных контакта."""


class ContactNotFoundError(PhoneBookError):
    """Ошибка отсутствия контакта с указанным ID."""


class StorageError(PhoneBookError):
    """Базовый класс ошибок файлового хранилища."""


class FileReadError(StorageError):
    """Ошибка чтения контактов из файла."""


class FileWriteError(StorageError):
    """Ошибка записи контактов в файл."""


class InvalidDataFormatError(FileReadError):
    """Ошибка некорректной структуры файла контактов."""
