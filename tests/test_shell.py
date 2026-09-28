"""Тесты REPL и встроенных команд."""

import io
import unittest
from unittest import mock

from shell_emulator.commands import ExitRequest
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
        with self.assertRaises(ExitRequest) as ctx:
            self.shell.execute("exit")
        self.assertEqual(ctx.exception.code, 0)

    def test_exit_with_code(self):
        """exit N завершает работу с кодом N."""
        with self.assertRaises(ExitRequest) as ctx:
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


if __name__ == "__main__":
    unittest.main()
