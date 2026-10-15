"""Тесты команд этапов 4 и 5: ls, cd, head, clear, cp, chmod."""

import base64
import io
import json
import os
import tempfile
import unittest

from shell_emulator.shell import Shell
from shell_emulator.vfs import load_vfs, node_path


def file_node(text, mode=None):
    """Вернуть JSON-описание файла с текстом ``text``."""
    node = {"type": "file", "data": base64.b64encode(text).decode()}
    if mode is not None:
        node["mode"] = mode
    return node


def dir_node(children):
    """Вернуть JSON-описание каталога с узлами ``children``."""
    return {"type": "dir", "children": children}


TEST_VFS = dir_node({
    "motd": file_node(b"Hello\n"),
    "home": dir_node({"user": dir_node({
        "docs": dir_node({"report.txt": file_node(b"line 1\nline 2\n")}),
        "long.txt": file_node(
            "".join(f"{i}\n" for i in range(1, 16)).encode()),
        "secret.txt": file_node(b"x\n", mode="600"),
    })}),
    "empty": dir_node({}),
})


class CommandsTest(unittest.TestCase):
    """Проверки команд на тестовой VFS."""

    def setUp(self):
        """Загрузить тестовую VFS в оболочку с перехватом вывода."""
        handle, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(TEST_VFS, file)
        self.addCleanup(os.remove, path)
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.shell = Shell(stdout=self.out, stderr=self.err)
        self.shell.user = "student"
        self.shell.host = "pc"
        self.shell.set_vfs(load_vfs(path))

    def run_command(self, line):
        """Выполнить команду и вернуть (успех, вывод, ошибки)."""
        self.out.seek(0)
        self.out.truncate()
        self.err.seek(0)
        self.err.truncate()
        ok = self.shell.execute(line)
        return ok, self.out.getvalue(), self.err.getvalue()

    def test_ls_current_dir(self):
        """ls выводит содержимое по алфавиту, каталоги с /."""
        self.assertEqual(self.run_command("ls")[1], "empty/\nhome/\nmotd\n")

    def test_ls_paths(self):
        """ls принимает относительные и абсолютные пути и путь к файлу."""
        self.assertEqual(self.run_command("ls home/user")[1],
                         "docs/\nlong.txt\nsecret.txt\n")
        self.assertEqual(self.run_command("ls /home/user/docs")[1],
                         "report.txt\n")
        self.assertEqual(self.run_command("ls /motd")[1], "motd\n")
        self.assertEqual(self.run_command("ls empty")[1], "")

    def test_ls_long_format(self):
        """ls -l выводит права доступа перед именем."""
        self.assertEqual(self.run_command("ls -l home/user")[1],
                         "drwxr-xr-x docs/\n-rw-r--r-- long.txt\n"
                         "-rw------- secret.txt\n")

    def test_ls_errors(self):
        """Ошибки ls: нет пути, неизвестный ключ, лишний аргумент."""
        self.assertIn("ls: nowhere: No such file or directory",
                      self.run_command("ls nowhere")[2])
        self.assertIn("ls: invalid option -- 'x'",
                      self.run_command("ls -x")[2])
        self.assertIn("ls: too many arguments",
                      self.run_command("ls home empty")[2])

    def test_cd_and_prompt(self):
        """cd меняет каталог, приглашение показывает путь."""
        self.run_command("cd home/user/docs")
        self.assertEqual(self.shell.prompt(), "student@pc:/home/user/docs$ ")
        self.run_command("cd ..")
        self.assertEqual(node_path(self.shell.cwd), "/home/user")
        self.run_command("cd ./docs/../../..")
        self.assertEqual(node_path(self.shell.cwd), "/")
        self.run_command("cd /home")
        self.run_command("cd")
        self.assertEqual(node_path(self.shell.cwd), "/")

    def test_cd_errors(self):
        """Ошибки cd: файл, нет пути, лишний аргумент."""
        self.assertIn("cd: motd: Not a directory",
                      self.run_command("cd motd")[2])
        self.assertIn("cd: nowhere: No such file or directory",
                      self.run_command("cd nowhere")[2])
        self.assertIn("cd: too many arguments",
                      self.run_command("cd a b")[2])
        self.assertEqual(node_path(self.shell.cwd), "/")

    def test_head_default_and_n(self):
        """head выводит 10 строк по умолчанию или -n строк."""
        out = self.run_command("head home/user/long.txt")[1]
        self.assertEqual(out, "".join(f"{i}\n" for i in range(1, 11)))
        self.assertEqual(self.run_command("head -n 2 home/user/long.txt")[1],
                         "1\n2\n")
        self.assertEqual(self.run_command("head -n 0 motd")[1], "")

    def test_head_errors(self):
        """Ошибки head: нет файла, каталог, плохое число, нет числа."""
        self.assertIn("head: missing file operand",
                      self.run_command("head")[2])
        self.assertIn("head: /home: Is a directory",
                      self.run_command("head /home")[2])
        self.assertIn("head: invalid number of lines: 'abc'",
                      self.run_command("head -n abc motd")[2])
        self.assertIn("option requires an argument -- 'n'",
                      self.run_command("head -n")[2])
        self.assertIn("head: nowhere: No such file or directory",
                      self.run_command("head nowhere")[2])

    def test_clear(self):
        """clear выводит управляющую последовательность очистки экрана."""
        ok, out, _ = self.run_command("clear")
        self.assertTrue(ok)
        self.assertEqual(out, "\033[H\033[2J")
        self.assertIn("clear: too many arguments",
                      self.run_command("clear x")[2])

    def test_cp_file(self):
        """cp копирует файл в новый файл и в существующий каталог."""
        self.run_command("cd /home/user")
        self.assertTrue(self.run_command("cp docs/report.txt copy.txt")[0])
        self.assertTrue(self.run_command("cp secret.txt docs")[0])
        self.assertEqual(self.run_command("ls docs")[1],
                         "report.txt\nsecret.txt\n")
        self.assertEqual(self.run_command("head copy.txt")[1],
                         "line 1\nline 2\n")
        self.assertEqual(self.run_command("ls -l docs/secret.txt")[1],
                         "-rw------- secret.txt\n")

    def test_cp_overwrite_and_absolute(self):
        """cp перезаписывает файл и работает с абсолютными путями."""
        self.run_command("cp /home/user/docs/report.txt /motd")
        self.assertEqual(self.run_command("head /motd")[1],
                         "line 1\nline 2\n")
        self.run_command("cp /motd /new.txt")
        self.assertIn("new.txt", self.run_command("ls /")[1])

    def test_cp_recursive_is_deep_copy(self):
        """cp -r копирует каталог целиком, копия независима."""
        self.run_command("cd /home/user")
        self.assertTrue(self.run_command("cp -r docs backup")[0])
        self.run_command("cp long.txt backup/report.txt")
        self.assertEqual(self.run_command("head docs/report.txt")[1],
                         "line 1\nline 2\n")
        self.assertEqual(self.run_command("ls backup")[1], "report.txt\n")

    def test_cp_errors(self):
        """Ошибки cp: аргументы, нет пути, каталог без -r, сам в себя."""
        self.run_command("cd /home/user")
        cases = {
            "cp": "cp: missing file operand",
            "cp long.txt": "cp: missing destination file operand",
            "cp a b c": "cp: too many arguments",
            "cp -x a b": "cp: invalid option -- 'x'",
            "cp nowhere b.txt": "cp: nowhere: No such file or directory",
            "cp docs x": "-r not specified; omitting directory 'docs'",
            "cp long.txt nowhere/b.txt":
                "cp: nowhere/b.txt: No such file or directory",
            "cp -r docs docs/x": "into itself",
            "cp long.txt .": "are the same file",
            "cp -r docs long.txt": "cannot overwrite non-directory",
        }
        for line, message in cases.items():
            ok, _, err = self.run_command(line)
            self.assertFalse(ok, line)
            self.assertIn(message, err, line)

    def test_cp_does_not_overwrite_directory(self):
        """Повторное копирование каталога в то же место - ошибка."""
        self.run_command("cd /home/user")
        self.assertTrue(self.run_command("cp -r docs /empty")[0])
        ok, _, err = self.run_command("cp -r docs /empty")
        self.assertFalse(ok)
        self.assertIn("cannot overwrite directory 'docs'", err)

    def test_cp_does_not_touch_file_on_disk(self):
        """cp меняет только VFS в памяти, а не JSON-файл."""
        before = json.dumps(TEST_VFS, sort_keys=True)
        self.run_command("cp -r /home /home_copy")
        self.assertEqual(json.dumps(TEST_VFS, sort_keys=True), before)
        self.assertIn("home_copy/", self.run_command("ls /")[1])

    def test_chmod(self):
        """chmod меняет права файла и каталога."""
        self.assertTrue(self.run_command("chmod 600 motd")[0])
        self.assertTrue(self.run_command("chmod 700 home")[0])
        self.assertEqual(self.run_command("ls -l /")[1],
                         "drwxr-xr-x empty/\ndrwx------ home/\n"
                         "-rw------- motd\n")

    def test_chmod_errors(self):
        """Ошибки chmod: нет операнда, неверные права, нет пути."""
        cases = {
            "chmod": "chmod: missing operand",
            "chmod 600": "chmod: missing operand",
            "chmod 600 a b": "chmod: too many arguments",
            "chmod abc motd": "chmod: invalid mode: 'abc'",
            "chmod 999 motd": "chmod: invalid mode: '999'",
            "chmod 6000 motd": "chmod: invalid mode: '6000'",
            "chmod 600 nowhere": "chmod: nowhere: No such file or directory",
        }
        for line, message in cases.items():
            ok, _, err = self.run_command(line)
            self.assertFalse(ok, line)
            self.assertIn(message, err, line)


if __name__ == "__main__":
    unittest.main()
