"""Цикл REPL (read-eval-print loop) эмулятора."""

import getpass
import socket
import sys

from shell_emulator.commands import COMMANDS, CommandError, ExitRequest
from shell_emulator.parser import ParseError, parse

SHELL_NAME = "shell"
HOME_MARK = "~"
DEFAULT_USER = "user"


def current_user():
    """Вернуть имя текущего пользователя ОС."""
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return DEFAULT_USER


def current_host():
    """Вернуть короткое имя хоста ОС (до первой точки)."""
    return socket.gethostname().split(".")[0]


class Shell:
    """Интерактивная оболочка с приглашением ``user@host:~$``."""

    def __init__(self, stdout=None, stderr=None):
        """Создать оболочку.

        Args:
            stdout: поток для обычного вывода (по умолчанию sys.stdout).
            stderr: поток для ошибок (по умолчанию sys.stderr).
        """
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.user = current_user()
        self.host = current_host()
        self.cwd = HOME_MARK
        self.commands = dict(COMMANDS)

    def prompt(self):
        """Сформировать приглашение к вводу по данным ОС."""
        return f"{self.user}@{self.host}:{self.cwd}$ "

    def error(self, message):
        """Вывести сообщение об ошибке в поток ошибок."""
        print(f"{SHELL_NAME}: {message}", file=self.stderr)

    def execute(self, line):
        """Разобрать и выполнить одну командную строку.

        Raises:
            ExitRequest: если пользователь вызвал ``exit``.
        """
        try:
            tokens = parse(line)
        except ParseError as exc:
            self.error(f"syntax error: {exc}")
            return
        if not tokens:
            return
        name, args = tokens[0], tokens[1:]
        handler = self.commands.get(name)
        if handler is None:
            self.error(f"{name}: command not found")
            return
        try:
            output = handler(self, args)
        except CommandError as exc:
            self.error(f"{name}: {exc}")
            return
        if output is not None:
            print(output, file=self.stdout)

    def read_line(self):
        """Прочитать строку ввода; вернуть ``None`` при EOF (Ctrl+D)."""
        try:
            return input(self.prompt())
        except EOFError:
            print("exit", file=self.stdout)
            return None

    def run(self):
        """Запустить REPL и вернуть код завершения."""
        while True:
            try:
                line = self.read_line()
                if line is None:
                    return 0
                self.execute(line)
            except KeyboardInterrupt:
                print(file=self.stdout)
            except ExitRequest as request:
                return request.code
