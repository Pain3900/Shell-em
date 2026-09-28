"""Точка входа: ``python -m shell_emulator [--cli]``."""

import argparse
import importlib.util
import sys

from shell_emulator.shell import Shell


def parse_args(argv):
    """Разобрать параметры командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog="shell_emulator",
        description="Эмулятор командной оболочки UNIX.")
    parser.add_argument(
        "--cli", action="store_true",
        help="запустить в терминале вместо графического окна")
    return parser.parse_args(argv)


def run_cli():
    """Запустить REPL в терминале и вернуть код завершения."""
    if importlib.util.find_spec("readline") is not None:
        importlib.import_module("readline")
    return Shell().run()


def main(argv=None):
    """Запустить эмулятор в нужном режиме и вернуть код завершения."""
    args = parse_args(argv)
    if args.cli:
        return run_cli()
    from shell_emulator.gui import run_gui
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
