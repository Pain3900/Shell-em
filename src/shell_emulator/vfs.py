"""Виртуальная файловая система (VFS), загружаемая из JSON-файла.

Формат JSON: корень - объект-каталог. Каталог описывается как
``{"type": "dir", "children": {имя: узел, ...}}``, файл - как
``{"type": "file", "data": "<base64>"}``. Содержимое файлов хранится
в base64, поэтому в VFS можно хранить и двоичные данные. У любого узла
можно указать права ``"mode": "755"``; по умолчанию у каталогов 755,
у файлов 644.

Вся VFS загружается в память; исходный файл только читается.
"""

import base64
import binascii
import json

DIR_TYPE = "dir"
FILE_TYPE = "file"
MOTD_NAME = "motd"
SEPARATOR = "/"
CURRENT_DIR = "."
PARENT_DIR = ".."
DEFAULT_DIR_MODE = 0o755
DEFAULT_FILE_MODE = 0o644
OCTAL_BASE = 8
MODE_DIGITS = 3
PERMISSION_LETTERS = "rwx"
PERMISSION_BITS = 9


class VfsError(Exception):
    """Ошибка загрузки VFS."""


class VfsFile:
    """Файл VFS: имя, содержимое в байтах, права и родительский каталог."""

    def __init__(self, name, data, mode=DEFAULT_FILE_MODE):
        """Создать файл с именем ``name`` и содержимым ``data``."""
        self.name = name
        self.data = data
        self.mode = mode
        self.parent = None


class VfsDir:
    """Каталог VFS: имя, вложенные узлы, права и родительский каталог."""

    def __init__(self, name, mode=DEFAULT_DIR_MODE):
        """Создать пустой каталог с именем ``name``."""
        self.name = name
        self.children = {}
        self.mode = mode
        self.parent = None

    def add(self, node):
        """Добавить узел ``node`` в каталог и вернуть его."""
        node.parent = self
        self.children[node.name] = node
        return node


def load_vfs(path):
    """Загрузить VFS из JSON-файла в память и вернуть корневой каталог.

    Raises:
        VfsError: если файл не открывается, не является корректным
            JSON или не соответствует формату VFS.
    """
    try:
        with open(path, encoding="utf-8") as file:
            raw = json.load(file)
    except OSError as exc:
        raise VfsError(f"cannot open '{path}': {exc.strerror}") from None
    except json.JSONDecodeError as exc:
        raise VfsError(f"invalid JSON in '{path}': {exc.msg}, "
                       f"line {exc.lineno}") from None
    root = build_node("/", raw)
    if not isinstance(root, VfsDir):
        raise VfsError("root of VFS must be a directory")
    return root


def build_node(name, raw):
    """Построить узел VFS (файл или каталог) из JSON-объекта."""
    if not isinstance(raw, dict):
        raise VfsError(f"'{name}': node must be a JSON object")
    node_type = raw.get("type")
    if node_type == DIR_TYPE:
        node = build_dir(name, raw)
    elif node_type == FILE_TYPE:
        node = build_file(name, raw)
    else:
        raise VfsError(f"'{name}': unknown node type {node_type!r}")
    if "mode" in raw:
        node.mode = parse_mode(raw["mode"], name)
    return node


def parse_mode(value, name):
    """Преобразовать права вида ``"755"`` в число.

    Raises:
        VfsError: если права не являются тремя восьмеричными цифрами.
    """
    if not isinstance(value, str) or len(value) != MODE_DIGITS:
        raise VfsError(f"'{name}': mode must be 3 octal digits")
    try:
        return int(value, OCTAL_BASE)
    except ValueError:
        raise VfsError(f"'{name}': mode must be 3 octal digits") from None


def build_dir(name, raw):
    """Построить каталог VFS со всеми вложенными узлами."""
    children = raw.get("children", {})
    if not isinstance(children, dict):
        raise VfsError(f"'{name}': children must be a JSON object")
    directory = VfsDir(name)
    for child_name, child_raw in children.items():
        directory.add(build_node(child_name, child_raw))
    return directory


def build_file(name, raw):
    """Построить файл VFS, раскодировав содержимое из base64."""
    encoded = raw.get("data", "")
    if not isinstance(encoded, str):
        raise VfsError(f"'{name}': data must be a base64 string")
    try:
        data = base64.b64decode(encoded, validate=True)
    except binascii.Error:
        raise VfsError(f"'{name}': data is not valid base64") from None
    return VfsFile(name, data)


def read_motd(root):
    """Вернуть текст файла motd из корня VFS или None, если его нет."""
    node = root.children.get(MOTD_NAME)
    if not isinstance(node, VfsFile):
        return None
    return node.data.decode("utf-8", errors="replace")


def vfs_stats(node):
    """Посчитать каталоги, файлы и число уровней в дереве VFS.

    Returns:
        Кортеж ``(каталоги, файлы, уровни)``. Корень - первый уровень,
        каждый вложенный файл или каталог добавляет ещё один.
    """
    if isinstance(node, VfsFile):
        return 0, 1, 1
    dirs, files, depth = 1, 0, 0
    for child in node.children.values():
        child_dirs, child_files, child_depth = vfs_stats(child)
        dirs += child_dirs
        files += child_files
        depth = max(depth, child_depth)
    return dirs, files, depth + 1


def resolve(root, cwd, path):
    """Найти узел по абсолютному или относительному (от ``cwd``) пути.

    Returns:
        Найденный узел или None, если такого пути нет.
    """
    node = root if path.startswith(SEPARATOR) else cwd
    for part in path.split(SEPARATOR):
        if part in ("", CURRENT_DIR):
            continue
        if part == PARENT_DIR:
            node = node.parent or node
            continue
        if not isinstance(node, VfsDir) or part not in node.children:
            return None
        node = node.children[part]
    return node


def node_path(node):
    """Вернуть абсолютный путь узла; для корня - ``/``."""
    parts = []
    while node.parent is not None:
        parts.append(node.name)
        node = node.parent
    return SEPARATOR + SEPARATOR.join(reversed(parts))


def mode_string(node):
    """Вернуть права узла в виде ``drwxr-xr-x`` или ``-rw-r--r--``.

    Права 0o755 в двоичном виде - 111101101: каждая единица заменяется
    соответствующей буквой из ``rwxrwxrwx``, каждый ноль - дефисом.
    """
    kind = "d" if isinstance(node, VfsDir) else "-"
    bits = format(node.mode, f"0{PERMISSION_BITS}b")
    letters = PERMISSION_LETTERS * MODE_DIGITS
    return kind + "".join(letter if bit == "1" else "-"
                          for letter, bit in zip(letters, bits))
