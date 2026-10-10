"""Тесты загрузки виртуальной файловой системы."""

import base64
import json
import os
import tempfile
import unittest

from shell_emulator.vfs import (VfsDir, VfsError, VfsFile, load_vfs,
                                read_motd, vfs_stats)


def encode(data):
    """Закодировать байты в строку base64."""
    return base64.b64encode(data).decode()


def file_node(data):
    """Вернуть JSON-описание файла с содержимым ``data``."""
    return {"type": "file", "data": encode(data)}


def dir_node(children):
    """Вернуть JSON-описание каталога с узлами ``children``."""
    return {"type": "dir", "children": children}


class LoadVfsTest(unittest.TestCase):
    """Проверки функции load_vfs."""

    def write_vfs(self, content):
        """Записать VFS во временный файл и вернуть путь."""
        handle, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            if isinstance(content, str):
                file.write(content)
            else:
                json.dump(content, file)
        self.addCleanup(os.remove, path)
        return path

    def test_minimal(self):
        """Минимальная VFS - пустой корневой каталог."""
        root = load_vfs(self.write_vfs(dir_node({})))
        self.assertIsInstance(root, VfsDir)
        self.assertEqual(root.children, {})
        self.assertEqual(vfs_stats(root), (1, 0, 1))
        self.assertIsNone(read_motd(root))

    def test_several_files(self):
        """Несколько файлов в корне, motd читается как текст."""
        root = load_vfs(self.write_vfs(dir_node({
            "motd": file_node("Привет!\n".encode("utf-8")),
            "a.txt": file_node(b"a"),
            "b.txt": file_node(b"b"),
        })))
        self.assertEqual(vfs_stats(root), (1, 3, 2))
        self.assertEqual(read_motd(root), "Привет!\n")

    def test_three_levels(self):
        """Вложенные каталоги загружаются на всю глубину."""
        root = load_vfs(self.write_vfs(dir_node({
            "home": dir_node({"user": dir_node({
                "notes.txt": file_node(b"text")})}),
        })))
        notes = root.children["home"].children["user"].children["notes.txt"]
        self.assertIsInstance(notes, VfsFile)
        self.assertEqual(notes.data, b"text")
        self.assertEqual(vfs_stats(root), (3, 1, 4))

    def test_binary_data(self):
        """Двоичные данные из base64 сохраняются без изменений."""
        data = bytes(range(256))
        root = load_vfs(self.write_vfs(dir_node({"x.bin": file_node(data)})))
        self.assertEqual(root.children["x.bin"].data, data)

    def test_motd_directory_ignored(self):
        """Каталог с именем motd не считается сообщением дня."""
        root = load_vfs(self.write_vfs(dir_node({"motd": dir_node({})})))
        self.assertIsNone(read_motd(root))

    def test_missing_file(self):
        """Несуществующий файл VFS - ошибка."""
        with self.assertRaisesRegex(VfsError, "cannot open"):
            load_vfs("/no/such/vfs.json")

    def test_invalid_json(self):
        """Некорректный JSON - ошибка."""
        with self.assertRaisesRegex(VfsError, "invalid JSON"):
            load_vfs(self.write_vfs('{"type": "dir",'))

    def test_unknown_type(self):
        """Неизвестный тип узла - ошибка."""
        with self.assertRaisesRegex(VfsError, "unknown node type"):
            load_vfs(self.write_vfs(dir_node({"x": {"type": "link"}})))

    def test_invalid_base64(self):
        """Содержимое файла не в base64 - ошибка."""
        bad = {"type": "file", "data": "not base64!"}
        with self.assertRaisesRegex(VfsError, "base64"):
            load_vfs(self.write_vfs(dir_node({"x": bad})))

    def test_root_must_be_dir(self):
        """Корень VFS должен быть каталогом."""
        with self.assertRaisesRegex(VfsError, "root"):
            load_vfs(self.write_vfs(file_node(b"x")))

    def test_children_must_be_object(self):
        """Поле children должно быть JSON-объектом."""
        with self.assertRaisesRegex(VfsError, "children"):
            load_vfs(self.write_vfs({"type": "dir", "children": []}))


if __name__ == "__main__":
    unittest.main()
