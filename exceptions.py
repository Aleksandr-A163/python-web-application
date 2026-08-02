"""Custom exceptions used by the phone book application."""


class PhoneBookError(Exception):
    """Base class for expected application errors."""


class ValidationError(PhoneBookError):
    """Raised when contact data is invalid."""


class ContactNotFoundError(PhoneBookError):
    """Raised when a contact with the requested ID does not exist."""


class StorageError(PhoneBookError):
    """Base class for file storage errors."""


class FileReadError(StorageError):
    """Raised when contacts cannot be read from a file."""


class FileWriteError(StorageError):
    """Raised when contacts cannot be written to a file."""


class InvalidDataFormatError(FileReadError):
    """Raised when the contacts file has an invalid structure."""
