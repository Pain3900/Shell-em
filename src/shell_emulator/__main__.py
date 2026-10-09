"""Точка входа: ``python -m shell_emulator [--vfs ПУТЬ] [--script ПУТЬ]``."""

import argparse
import importlib.util
import sys

from shell_emulator.commands import format_config
from shell_emulator.shell import Shell

DEBUG_PREFIX = "[debug] "


def parse_args(argv=None):
    """Разобрать параметры командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog="shell_emulator",
        description="Эмулятор командной оболочки UNIX.")
    parser.add_argument(
        "--vfs", help="путь к физическому расположению VFS")
    parser.add_argument(
        "--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def enable_line_editing():
    """Включить историю ввода стрелками, если доступен модуль readline."""
    if importlib.util.find_spec("readline") is not None:
        importlib.import_module("readline")


def main(argv=None):
    """Запустить эмулятор и вернуть код завершения."""
    args = parse_args(argv)
    config = {"vfs": args.vfs, "script": args.script}
    for line in format_config(config):
        print(DEBUG_PREFIX + line)
    enable_line_editing()
    shell = Shell(config=config)
    if args.script is not None:
        try:
            shell.run_script(args.script)
        except SystemExit as request:
            return request.code
    return shell.run()


if __name__ == "__main__":
    sys.exit(main())
