"""Совместимая точка запуска консольного приложения."""

from phonebook.cli.application import main


if __name__ == "__main__":  # pragma: no cover - запуск из командной строки
    main()
