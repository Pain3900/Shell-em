"""Встроенные команды эмулятора.

Каждая команда - функция ``(shell, args)``, которая возвращает текст
для вывода (или ``None``) либо возбуждает :class:`CommandError`.
"""

MAX_EXIT_ARGS = 1
EXIT_CODE_MODULO = 256


class CommandError(Exception):
    """Ошибка выполнения команды, сообщение показывается пользователю."""


class ExitRequest(Exception):
    """Запрос на завершение работы эмулятора.

    Attributes:
        code: код возврата эмулятора.
    """

    def __init__(self, code=0):
        """Сохранить код возврата ``code``."""
        super().__init__(code)
        self.code = code


def stub(name, args):
    """Сформировать вывод команды-заглушки: имя и аргументы."""
    return f"{name}: args={args!r}"


def cmd_ls(shell, args):
    """Заглушка команды ``ls``: выводит имя и аргументы."""
    del shell
    return stub("ls", args)


def cmd_cd(shell, args):
    """Заглушка команды ``cd``: выводит имя и аргументы."""
    del shell
    return stub("cd", args)


def cmd_exit(shell, args):
    """Команда ``exit [код]``: завершить работу эмулятора.

    Raises:
        ExitRequest: всегда при корректных аргументах.
        CommandError: если аргументов больше одного
            или код не является целым числом.
    """
    del shell
    if len(args) > MAX_EXIT_ARGS:
        raise CommandError("too many arguments")
    if not args:
        raise ExitRequest(0)
    try:
        code = int(args[0])
    except ValueError:
        raise CommandError(
            f"{args[0]}: numeric argument required") from None
    raise ExitRequest(code % EXIT_CODE_MODULO)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}
