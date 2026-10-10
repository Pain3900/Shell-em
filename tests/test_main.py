"""Тесты параметров командной строки и запуска эмулятора."""

import base64
import contextlib
import io
import json
import os
import tempfile
import unittest

from shell_emulator.__main__ import main, parse_args


def write_temp(text, suffix):
    """Записать текст во временный файл и вернуть путь к нему."""
    handle, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(handle, "w", encoding="utf-8") as file:
        file.write(text)
    return path


def run_main(argv):
    """Запустить main, вернуть код завершения, вывод и ошибки."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class ParseArgsTest(unittest.TestCase):
    """Проверки разбора параметров командной строки."""

    def test_defaults(self):
        """Без параметров оба пути не заданы."""
        args = parse_args([])
        self.assertIsNone(args.vfs)
        self.assertIsNone(args.script)

    def test_all_options(self):
        """Параметры --vfs и --script сохраняются."""
        args = parse_args(["--vfs", "vfs.json", "--script", "start.txt"])
        self.assertEqual(args.vfs, "vfs.json")
        self.assertEqual(args.script, "start.txt")


class MainTest(unittest.TestCase):
    """Проверки запуска эмулятора с VFS и стартовым скриптом."""

    def setUp(self):
        """Создать временные VFS и стартовый скрипт."""
        motd = base64.b64encode(b"Hello from motd\n").decode()
        vfs = {"type": "dir", "children": {
            "motd": {"type": "file", "data": motd}}}
        self.vfs = write_temp(json.dumps(vfs), ".json")
        self.script = write_temp("conf-dump\nexit 3\n", ".txt")
        self.addCleanup(os.remove, self.vfs)
        self.addCleanup(os.remove, self.script)

    def test_debug_motd_and_script(self):
        """Печатаются параметры, сведения о VFS, motd, затем скрипт."""
        code, out, _ = run_main(["--vfs", self.vfs,
                                 "--script", self.script])
        self.assertEqual(code, 3)
        self.assertIn(f"[debug] vfs={self.vfs}", out)
        self.assertIn(f"[debug] script={self.script}", out)
        self.assertIn("[debug] vfs loaded: dirs=1, files=1", out)
        self.assertIn("Hello from motd", out)
        self.assertIn(f"vfs={self.vfs}\nscript=", out)

    def test_vfs_error_stops_start(self):
        """Ошибка загрузки VFS завершает эмулятор с кодом 1."""
        code, out, err = run_main(["--vfs", "/no/such/vfs.json",
                                   "--script", self.script])
        self.assertEqual(code, 1)
        self.assertIn("vfs: cannot open", err)
        self.assertNotIn("conf-dump", out)


if __name__ == "__main__":
    unittest.main()
