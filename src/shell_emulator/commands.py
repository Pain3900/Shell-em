"""Встроенные команды эмулятора.

Каждая команда - функция ``(shell, args)``, которая возвращает текст
для вывода (или ``None``) либо возбуждает :class:`CommandError`.
"""

from shell_emulator.vfs import (VfsDir, copy_node, is_inside, mode_string,
                                resolve)

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
RECURSIVE_FLAG = "r"
CP_OPERANDS = 2
CHMOD_OPERANDS = 2
MODE_DIGITS = 3
OCTAL_DIGITS = "01234567"
OCTAL_BASE = 8
SEPARATOR = "/"
SPECIAL_NAMES = ("", ".", "..")


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


def parse_cp_args(args):
    """Разобрать ``cp [-r] ИСТОЧНИК НАЗНАЧЕНИЕ``.

    Returns:
        Кортеж (флаг -r, путь источника, путь назначения).
    """
    flags, operands = split_options(args)
    unknown = sorted(flags - {RECURSIVE_FLAG})
    if unknown:
        raise CommandError(f"invalid option -- '{unknown[0]}'")
    if not operands:
        raise CommandError("missing file operand")
    if len(operands) < CP_OPERANDS:
        raise CommandError("missing destination file operand")
    if len(operands) > CP_OPERANDS:
        raise CommandError("too many arguments")
    return RECURSIVE_FLAG in flags, operands[0], operands[1]


def cp_target(shell, source, path):
    """Найти каталог и имя для копии по пути назначения.

    Если назначение - существующий каталог, копия кладётся в него
    под именем источника; иначе последняя часть пути - новое имя.
    """
    dest = resolve(shell.vfs, shell.cwd, path)
    if isinstance(dest, VfsDir):
        return dest, source.name
    dir_path, _, name = path.rpartition(SEPARATOR)
    if path.startswith(SEPARATOR) and not dir_path:
        dir_path = SEPARATOR
    directory = resolve(shell.vfs, shell.cwd, dir_path or ".")
    if not isinstance(directory, VfsDir) or name in SPECIAL_NAMES:
        raise CommandError(f"{path}: No such file or directory")
    return directory, name


def check_cp_target(source, directory, name, source_path):
    """Проверить, что копию можно положить в ``directory/name``."""
    old = directory.children.get(name)
    if old is source:
        raise CommandError(f"'{source_path}' and destination "
                           "are the same file")
    if isinstance(old, VfsDir):
        raise CommandError(f"cannot overwrite directory '{name}'")
    if old is not None and isinstance(source, VfsDir):
        raise CommandError(f"cannot overwrite non-directory '{name}' "
                           "with directory")
    if isinstance(source, VfsDir) and is_inside(directory, source):
        raise CommandError(f"cannot copy a directory, '{source_path}', "
                           "into itself")


def cmd_cp(shell, args):
    """Команда ``cp [-r] ИСТОЧНИК НАЗНАЧЕНИЕ``: копирование в памяти.

    Raises:
        CommandError: неверные аргументы, нет источника или назначения,
            каталог без -r, копирование каталога в самого себя.
    """
    recursive, source_path, dest_path = parse_cp_args(args)
    source = find_node(shell, source_path)
    if isinstance(source, VfsDir) and not recursive:
        raise CommandError(f"-r not specified; omitting directory "
                           f"'{source_path}'")
    directory, name = cp_target(shell, source, dest_path)
    check_cp_target(source, directory, name, source_path)
    copy = copy_node(source)
    copy.name = name
    directory.add(copy)
    return None


def parse_mode(text):
    """Преобразовать права из трёх восьмеричных цифр в число.

    Raises:
        CommandError: если это не три восьмеричные цифры.
    """
    if len(text) != MODE_DIGITS or any(c not in OCTAL_DIGITS for c in text):
        raise CommandError(f"invalid mode: '{text}'")
    return int(text, OCTAL_BASE)


def cmd_chmod(shell, args):
    """Команда ``chmod РЕЖИМ ПУТЬ``: изменить права узла в памяти.

    Raises:
        CommandError: неверное число аргументов, права или путь.
    """
    if len(args) < CHMOD_OPERANDS:
        raise CommandError("missing operand")
    if len(args) > CHMOD_OPERANDS:
        raise CommandError("too many arguments")
    mode = parse_mode(args[0])
    find_node(shell, args[1]).mode = mode
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
    "cp": cmd_cp,
    "chmod": cmd_chmod,
    "conf-dump": cmd_conf_dump,
    "exit": cmd_exit,
}
