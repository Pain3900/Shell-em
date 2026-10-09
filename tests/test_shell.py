"""Тесты REPL и встроенных команд."""

import io
import os
import tempfile
import unittest
from unittest import mock

from shell_emulator.shell import Shell


class ShellTest(unittest.TestCase):
    """Проверки класса Shell."""

    def setUp(self):
        """Создать оболочку с перехватом вывода."""
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.shell = Shell(stdout=self.out, stderr=self.err)
        self.shell.user = "student"
        self.shell.host = "pc"

    def test_prompt(self):
        """Приглашение имеет вид user@host:~$."""
        self.assertEqual(self.shell.prompt(), "student@pc:~$ ")

    def test_ls_stub(self):
        """Заглушка ls выводит имя и аргументы."""
        self.shell.execute('ls -l "my dir"')
        self.assertEqual(self.out.getvalue(),
                         "ls: args=['-l', 'my dir']\n")

    def test_cd_stub(self):
        """Заглушка cd выводит имя и аргументы."""
        self.shell.execute("cd /home")
        self.assertEqual(self.out.getvalue(), "cd: args=['/home']\n")

    def test_unknown_command(self):
        """Неизвестная команда даёт сообщение об ошибке."""
        self.shell.execute("foo bar")
        self.assertIn("foo: command not found", self.err.getvalue())

    def test_syntax_error(self):
        """Незакрытая кавычка даёт синтаксическую ошибку."""
        self.shell.execute('ls "abc')
        self.assertIn("syntax error", self.err.getvalue())

    def test_empty_line(self):
        """Пустая строка ничего не выводит."""
        self.shell.execute("   ")
        self.assertEqual(self.out.getvalue() + self.err.getvalue(), "")

    def test_exit_default_code(self):
        """exit без аргументов завершает работу с кодом 0."""
        with self.assertRaises(SystemExit) as ctx:
            self.shell.execute("exit")
        self.assertEqual(ctx.exception.code, 0)

    def test_exit_with_code(self):
        """exit N завершает работу с кодом N."""
        with self.assertRaises(SystemExit) as ctx:
            self.shell.execute("exit 3")
        self.assertEqual(ctx.exception.code, 3)

    def test_exit_bad_code(self):
        """exit с нечисловым аргументом сообщает об ошибке."""
        self.shell.execute("exit abc")
        self.assertIn("numeric argument required", self.err.getvalue())

    def test_exit_too_many_args(self):
        """exit с двумя аргументами сообщает об ошибке."""
        self.shell.execute("exit 1 2")
        self.assertIn("too many arguments", self.err.getvalue())

    def test_run_until_exit(self):
        """REPL выполняет команды до exit и возвращает код."""
        lines = iter(["ls a", "exit 5", "ls b"])
        with mock.patch("builtins.input", lambda _: next(lines)):
            code = self.shell.run()
        self.assertEqual(code, 5)
        self.assertNotIn("'b'", self.out.getvalue())

    def test_run_eof(self):
        """Ctrl+D (EOF) завершает REPL с кодом 0."""
        with mock.patch("builtins.input", side_effect=EOFError):
            self.assertEqual(self.shell.run(), 0)

    def test_execute_status(self):
        """execute возвращает True при успехе и False при ошибке."""
        self.assertTrue(self.shell.execute("ls a"))
        self.assertFalse(self.shell.execute("foo"))
        self.assertFalse(self.shell.execute('ls "abc'))


class ConfDumpTest(unittest.TestCase):
    """Проверки служебной команды conf-dump."""

    def setUp(self):
        """Создать оболочку с параметрами и перехватом вывода."""
        self.out = io.StringIO()
        self.err = io.StringIO()
        config = {"vfs": "/data/vfs.json", "script": None}
        self.shell = Shell(config=config, stdout=self.out,
                           stderr=self.err)

    def test_conf_dump(self):
        """conf-dump выводит параметры в формате ключ=значение."""
        self.shell.execute("conf-dump")
        self.assertEqual(self.out.getvalue(),
                         "vfs=/data/vfs.json\nscript=(not set)\n")

    def test_conf_dump_extra_args(self):
        """conf-dump с аргументами сообщает об ошибке."""
        self.assertFalse(self.shell.execute("conf-dump x"))
        self.assertIn("too many arguments", self.err.getvalue())


class ScriptTest(unittest.TestCase):
    """Проверки выполнения стартового скрипта."""

    def setUp(self):
        """Создать оболочку с перехватом вывода."""
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.shell = Shell(stdout=self.out, stderr=self.err)
        self.shell.user = "student"
        self.shell.host = "pc"

    def write_script(self, text):
        """Записать текст скрипта во временный файл и вернуть путь."""
        handle, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_script_ok(self):
        """Команды скрипта печатаются с приглашением и выполняются."""
        path = self.write_script('ls -l\n\ncd "My Documents"\n')
        self.assertTrue(self.shell.run_script(path))
        self.assertEqual(self.out.getvalue(),
                         "student@pc:~$ ls -l\n"
                         "ls: args=['-l']\n"
                         'student@pc:~$ cd "My Documents"\n'
                         "cd: args=['My Documents']\n")

    def test_script_stops_at_first_error(self):
        """Скрипт останавливается на первой ошибке."""
        path = self.write_script("ls a\nfoo\nls b\n")
        self.assertFalse(self.shell.run_script(path))
        self.assertIn("error at line 2", self.err.getvalue())
        self.assertNotIn("ls b", self.out.getvalue())

    def test_script_missing_file(self):
        """Несуществующий скрипт даёт сообщение об ошибке."""
        self.assertFalse(self.shell.run_script("/no/such/script.txt"))
        self.assertIn("cannot open", self.err.getvalue())

    def test_script_exit(self):
        """Команда exit в скрипте завершает эмулятор."""
        path = self.write_script("ls a\nexit 2\nls b\n")
        with self.assertRaises(SystemExit) as ctx:
            self.shell.run_script(path)
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
