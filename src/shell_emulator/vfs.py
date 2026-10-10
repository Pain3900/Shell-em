"""Виртуальная файловая система (VFS), загружаемая из JSON-файла.

Формат JSON: корень - объект-каталог. Каталог описывается как
``{"type": "dir", "children": {имя: узел, ...}}``, файл - как
``{"type": "file", "data": "<base64>"}``. Содержимое файлов хранится
в base64, поэтому в VFS можно хранить и двоичные данные.

Вся VFS загружается в память; исходный файл только читается.
"""

import base64
import binascii
import json

DIR_TYPE = "dir"
FILE_TYPE = "file"
MOTD_NAME = "motd"


class VfsError(Exception):
    """Ошибка загрузки VFS."""


class VfsFile:
    """Файл VFS: имя и содержимое в байтах."""

    def __init__(self, name, data):
        """Создать файл с именем ``name`` и содержимым ``data``."""
        self.name = name
        self.data = data


class VfsDir:
    """Каталог VFS: имя и словарь вложенных узлов."""

    def __init__(self, name):
        """Создать пустой каталог с именем ``name``."""
        self.name = name
        self.children = {}


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
        return build_dir(name, raw)
    if node_type == FILE_TYPE:
        return build_file(name, raw)
    raise VfsError(f"'{name}': unknown node type {node_type!r}")


def build_dir(name, raw):
    """Построить каталог VFS со всеми вложенными узлами."""
    children = raw.get("children", {})
    if not isinstance(children, dict):
        raise VfsError(f"'{name}': children must be a JSON object")
    directory = VfsDir(name)
    for child_name, child_raw in children.items():
        directory.children[child_name] = build_node(child_name, child_raw)
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
