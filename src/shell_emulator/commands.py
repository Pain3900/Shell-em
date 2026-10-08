"""Встроенные команды эмулятора.

Каждая команда - функция ``(shell, args)``, которая возвращает текст
для вывода (или ``None``) либо возбуждает :class:`CommandError`.
"""

MAX_EXIT_ARGS = 1
EXIT_CODE_MODULO = 256
NOT_SET = "(not set)"


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


def format_config(config):
    """Вернуть параметры эмулятора в виде строк ``ключ=значение``."""
    lines = []
    for key, value in config.items():
        shown = NOT_SET if value is None else value
        lines.append(f"{key}={shown}")
    return lines


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


def cmd_conf_dump(shell, args):
    """Команда ``conf-dump``: вывести параметры эмулятора.

    Raises:
        CommandError: если переданы аргументы.
    """
    if args:
        raise CommandError("too many arguments")
    return "\n".join(format_config(shell.config))


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
    "conf-dump": cmd_conf_dump,
    "exit": cmd_exit,
}
