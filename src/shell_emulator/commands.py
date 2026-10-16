"""Встроенные команды эмулятора.

Каждая команда - функция ``(shell, args)``, которая возвращает текст
для вывода (или ``None``) либо возбуждает :class:`CommandError`.
"""

from shell_emulator.vfs import VfsDir, mode_string, resolve

MAX_EXIT_ARGS = 1
MAX_PATH_ARGS = 1
EXIT_CODE_MODULO = 256
NOT_SET = "(not set)"
OPTION_PREFIX = "-"
LONG_FORMAT_FLAG = "l"
LINES_OPTION = "-n"
LINES_OPTION_ARGS = 2
DEFAULT_HEAD_LINES = 10
CLEAR_SCREEN = "\033[H\033[2J"


class CommandError(Exception):
    """Ошибка выполнения команды, сообщение показывается пользователю."""


def format_config(config):
    """Вернуть параметры эмулятора в виде строк ``ключ=значение``."""
    lines = []
    for key, value in config.items():
        shown = NOT_SET if value is None else value
        lines.append(f"{key}={shown}")
    return lines


def find_node(shell, path):
    """Найти узел VFS по пути или возбудить CommandError."""
    node = resolve(shell.vfs, shell.cwd, path)
    if node is None:
        raise CommandError(f"{path}: No such file or directory")
    return node


def split_options(args):
    """Отделить ключи вида ``-l`` от остальных аргументов.

    Returns:
        Кортеж (набор букв ключей, список остальных аргументов).
    """
    flags = set()
    operands = []
    for arg in args:
        if arg.startswith(OPTION_PREFIX) and arg != OPTION_PREFIX:
            flags.update(arg[len(OPTION_PREFIX):])
        else:
            operands.append(arg)
    return flags, operands


def entry_name(node):
    """Вернуть имя узла для ls; к каталогам добавляется ``/``."""
    return node.name + ("/" if isinstance(node, VfsDir) else "")


def cmd_ls(shell, args):
    """Команда ``ls [-l] [ПУТЬ]``: содержимое каталога.

    Raises:
        CommandError: неизвестный ключ, лишний аргумент или нет пути.
    """
    flags, operands = split_options(args)
    unknown = sorted(flags - {LONG_FORMAT_FLAG})
    if unknown:
        raise CommandError(f"invalid option -- '{unknown[0]}'")
    if len(operands) > MAX_PATH_ARGS:
        raise CommandError("too many arguments")
    node = find_node(shell, operands[0]) if operands else shell.cwd
    nodes = [node]
    if isinstance(node, VfsDir):
        nodes = [node.children[name] for name in sorted(node.children)]
    lines = []
    for item in nodes:
        prefix = mode_string(item) + " " if LONG_FORMAT_FLAG in flags else ""
        lines.append(prefix + entry_name(item))
    return "\n".join(lines) or None


def cmd_cd(shell, args):
    """Команда ``cd [ПУТЬ]``: сменить текущий каталог (без пути - ``/``).

    Raises:
        CommandError: лишний аргумент, нет пути или путь - не каталог.
    """
    if len(args) > MAX_PATH_ARGS:
        raise CommandError("too many arguments")
    if not args:
        shell.cwd = shell.vfs
        return None
    node = find_node(shell, args[0])
    if not isinstance(node, VfsDir):
        raise CommandError(f"{args[0]}: Not a directory")
    shell.cwd = node
    return None


def parse_head_args(args):
    """Разобрать аргументы ``head [-n ЧИСЛО] ФАЙЛ``.

    Ключ ``-n`` занимает два аргумента: сам ключ и число строк.

    Returns:
        Кортеж (число строк, путь к файлу).
    """
    count = DEFAULT_HEAD_LINES
    operands = list(args)
    if operands and operands[0] == LINES_OPTION:
        if len(operands) < LINES_OPTION_ARGS:
            raise CommandError("option requires an argument -- 'n'")
        value = operands[1]
        if not value.isdigit():
            raise CommandError(f"invalid number of lines: '{value}'")
        count = int(value)
        operands = operands[LINES_OPTION_ARGS:]
    if not operands:
        raise CommandError("missing file operand")
    if len(operands) > MAX_PATH_ARGS:
        raise CommandError("too many arguments")
    return count, operands[0]


def cmd_head(shell, args):
    """Команда ``head [-n ЧИСЛО] ФАЙЛ``: первые строки файла.

    Raises:
        CommandError: неверные аргументы, нет файла или это каталог.
    """
    count, path = parse_head_args(args)
    node = find_node(shell, path)
    if isinstance(node, VfsDir):
        raise CommandError(f"{path}: Is a directory")
    lines = node.data.decode("utf-8", errors="replace").splitlines()
    return "\n".join(lines[:count]) or None


def cmd_clear(shell, args):
    """Команда ``clear``: очистить экран терминала.

    Raises:
        CommandError: если переданы аргументы.
    """
    if args:
        raise CommandError("too many arguments")
    shell.stdout.write(CLEAR_SCREEN)
    shell.stdout.flush()
    return None


def cmd_conf_dump(shell, args):
    """Команда ``conf-dump``: вывести параметры эмулятора.

    Raises:
        CommandError: если переданы аргументы.
    """
    if args:
        raise CommandError("too many arguments")
    return "\n".join(format_config(shell.config)) or None


def cmd_exit(shell, args):
    """Команда ``exit [код]``: завершить работу эмулятора.

    Raises:
        SystemExit: всегда при корректных аргументах.
        CommandError: если аргументов больше одного
            или код не является целым числом.
    """
    del shell
    if len(args) > MAX_EXIT_ARGS:
        raise CommandError("too many arguments")
    if not args:
        raise SystemExit(0)
    try:
        code = int(args[0])
    except ValueError:
        raise CommandError(
            f"{args[0]}: numeric argument required") from None
    raise SystemExit(code % EXIT_CODE_MODULO)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "head": cmd_head,
    "clear": cmd_clear,
    "conf-dump": cmd_conf_dump,
    "exit": cmd_exit,
}
