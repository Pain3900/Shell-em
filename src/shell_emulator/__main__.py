"""Точка входа: ``python -m shell_emulator``."""

import importlib.util
import sys

from shell_emulator.shell import Shell


def enable_line_editing():
    """Включить историю ввода стрелками, если доступен модуль readline."""
    if importlib.util.find_spec("readline") is not None:
        importlib.import_module("readline")


def main():
    """Запустить эмулятор в терминале и вернуть код завершения."""
    enable_line_editing()
    return Shell().run()


if __name__ == "__main__":
    sys.exit(main())
