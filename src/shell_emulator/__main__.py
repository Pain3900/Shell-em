"""Точка входа: ``python -m shell_emulator [--vfs ПУТЬ] [--script ПУТЬ]``."""

import argparse
import importlib.util
import sys

from shell_emulator.commands import format_config
from shell_emulator.shell import Shell
from shell_emulator.vfs import VfsError, load_vfs, read_motd, vfs_stats

DEBUG_PREFIX = "[debug] "
VFS_ERROR_CODE = 1


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


def start_vfs(shell, path):
    """Загрузить VFS в оболочку и вывести motd.

    Returns:
        True, если VFS загружена, иначе False (ошибка уже выведена).
    """
    try:
        shell.vfs = load_vfs(path)
    except VfsError as exc:
        shell.error(f"vfs: {exc}")
        return False
    dirs, files, levels = vfs_stats(shell.vfs)
    print(f"{DEBUG_PREFIX}vfs loaded: dirs={dirs}, files={files}, "
          f"levels={levels}")
    motd = read_motd(shell.vfs)
    if motd is not None:
        print(motd.rstrip("\n"))
    return True


def main(argv=None):
    """Запустить эмулятор и вернуть код завершения."""
    args = parse_args(argv)
    config = {"vfs": args.vfs, "script": args.script}
    for line in format_config(config):
        print(DEBUG_PREFIX + line)
    enable_line_editing()
    shell = Shell(config=config)
    if args.vfs is not None and not start_vfs(shell, args.vfs):
        return VFS_ERROR_CODE
    if args.script is not None:
        try:
            shell.run_script(args.script)
        except SystemExit as request:
            return request.code
    return shell.run()


if __name__ == "__main__":
    sys.exit(main())
