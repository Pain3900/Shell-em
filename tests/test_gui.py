"""Тесты графического окна (пропускаются, если нет дисплея)."""

import tkinter as tk
import unittest

from shell_emulator.gui import ShellWindow


class ShellWindowTest(unittest.TestCase):
    """Проверки окна ShellWindow."""

    def setUp(self):
        """Создать окно или пропустить тест без дисплея."""
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("нет графического дисплея")
        self.root.withdraw()
        self.window = ShellWindow(self.root)
        self.window.shell.user = "student"
        self.window.shell.host = "pc"

    def tearDown(self):
        """Закрыть окно, если оно ещё открыто."""
        try:
            self.root.destroy()
        except tk.TclError:
            self.root = None

    def type_command(self, line):
        """Ввести команду в строку cmd и нажать кнопку >."""
        self.window.entry.insert(0, line)
        self.window.submit()
        return self.window.output.get("1.0", tk.END)

    def test_command_echo_and_output(self):
        """Команда и её вывод появляются в области вывода."""
        text = self.type_command('ls "my dir"')
        self.assertIn("student@pc:~$ ls \"my dir\"", text)
        self.assertIn("ls: args=['my dir']", text)

    def test_error_is_shown(self):
        """Ошибка показывается в области вывода."""
        text = self.type_command("foo")
        self.assertIn("foo: command not found", text)

    def test_entry_cleared(self):
        """После выполнения строка ввода очищается."""
        self.type_command("cd /tmp")
        self.assertEqual(self.window.entry.get(), "")

    def test_history(self):
        """Стрелка вверх подставляет предыдущую команду."""
        self.type_command("ls a")
        self.window._browse_history(-1)
        self.assertEqual(self.window.entry.get(), "ls a")

    def test_exit_closes_window(self):
        """exit N закрывает окно и сохраняет код."""
        self.window.entry.insert(0, "exit 4")
        self.window.submit()
        with self.assertRaises(tk.TclError):
            self.root.winfo_exists()
        self.assertEqual(self.window.exit_code, 4)


if __name__ == "__main__":
    unittest.main()
