"""Тесты параметров командной строки и запуска эмулятора."""

import contextlib
import io
import os
import tempfile
import unittest

from shell_emulator.__main__ import main, parse_args


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
    """Проверки запуска эмулятора со стартовым скриптом."""

    def test_debug_output_and_script_exit(self):
        """При запуске печатаются параметры, затем выполняется скрипт."""
        handle, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write("conf-dump\nexit 3\n")
        self.addCleanup(os.remove, path)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--vfs", "vfs.json", "--script", path])
        self.assertEqual(code, 3)
        text = out.getvalue()
        self.assertIn("[debug] vfs=vfs.json", text)
        self.assertIn(f"[debug] script={path}", text)
        self.assertIn("vfs=vfs.json\nscript=", text)


if __name__ == "__main__":
    unittest.main()
