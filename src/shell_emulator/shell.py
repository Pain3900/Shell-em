"""Цикл REPL (read-eval-print loop) эмулятора."""

import getpass
import socket
import sys

from shell_emulator.commands import COMMANDS, CommandError
from shell_emulator.parse import ParseError, parse

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
    """Оболочка с приглашением ``user@host:~$``."""

    def __init__(self, config=None, stdout=None, stderr=None):
        """Создать оболочку.

        Args:
            config: параметры эмулятора (словарь ключ -> значение).
            stdout: поток для обычного вывода (по умолчанию sys.stdout).
            stderr: поток для ошибок (по умолчанию sys.stderr).
        """
        self.config = config if config is not None else {}
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.user = current_user()
        self.host = current_host()
        self.cwd = HOME_MARK
        self.vfs = None
        self.commands = dict(COMMANDS)

    def prompt(self):
        """Сформировать приглашение к вводу по данным ОС."""
        return f"{self.user}@{self.host}:{self.cwd}$ "

    def error(self, message):
        """Вывести сообщение об ошибке в поток ошибок."""
        self.stdout.flush()
        print(f"{SHELL_NAME}: {message}", file=self.stderr)

    def execute(self, line):
        """Разобрать и выполнить одну командную строку.

        Returns:
            True, если команда выполнена без ошибок, иначе False.

        Raises:
            SystemExit: если пользователь вызвал ``exit``.
        """
        try:
            tokens = parse(line)
        except ParseError as exc:
            self.error(f"syntax error: {exc}")
            return False
        if not tokens:
            return True
        name, args = tokens[0], tokens[1:]
        handler = self.commands.get(name)
        if handler is None:
            self.error(f"{name}: command not found")
            return False
        try:
            output = handler(self, args)
        except CommandError as exc:
            self.error(f"{name}: {exc}")
            return False
        if output is not None:
            print(output, file=self.stdout)
        return True

    def run_script(self, path):
        """Выполнить стартовый скрипт, остановившись на первой ошибке.

        Каждая команда печатается вместе с приглашением, затем её вывод,
        как будто её ввёл пользователь. Пустые строки пропускаются.

        Returns:
            True, если весь скрипт выполнен без ошибок, иначе False.

        Raises:
            SystemExit: если в скрипте встретилась команда ``exit``.
        """
        try:
            with open(path, encoding="utf-8") as file:
                lines = file.read().splitlines()
        except OSError as exc:
            self.error(f"script: cannot open '{path}': {exc.strerror}")
            return False
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            print(self.prompt() + line, file=self.stdout)
            if not self.execute(line):
                self.error(f"script: error at line {number}, stopped")
                return False
        return True

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
            except SystemExit as request:
                return request.code
