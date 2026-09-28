"""Тесты разбора командной строки."""

import unittest

from shell_emulator.parser import ParseError, parse


class ParseTest(unittest.TestCase):
    """Проверки функции parse."""

    def test_simple_words(self):
        """Слова разделяются любым количеством пробелов."""
        self.assertEqual(parse("ls  -l   /tmp"), ["ls", "-l", "/tmp"])

    def test_empty_line(self):
        """Пустая строка и пробелы дают пустой список."""
        self.assertEqual(parse(""), [])
        self.assertEqual(parse("   \t "), [])

    def test_double_quotes(self):
        """Пробелы внутри двойных кавычек не разделяют аргумент."""
        self.assertEqual(parse('cd "My Documents"'),
                         ["cd", "My Documents"])

    def test_single_quotes(self):
        """Внутри одинарных кавычек всё берётся буквально."""
        self.assertEqual(parse("ls 'a \"b\" \\c'"),
                         ["ls", 'a "b" \\c'])

    def test_quotes_inside_word(self):
        """Кавычки внутри слова склеиваются с соседним текстом."""
        self.assertEqual(parse('ls a"b c"d'), ["ls", "ab cd"])

    def test_empty_quotes(self):
        """Пустые кавычки дают пустой аргумент."""
        self.assertEqual(parse('ls "" \'\''), ["ls", "", ""])

    def test_escape_outside_quotes(self):
        """Обратный слеш экранирует пробел вне кавычек."""
        self.assertEqual(parse("cd My\\ Dir"), ["cd", "My Dir"])

    def test_escape_in_double_quotes(self):
        """В двойных кавычках экранируются только \" и \\."""
        self.assertEqual(parse('ls "a\\"b" "c\\d"'),
                         ["ls", 'a"b', "c\\d"])

    def test_unclosed_double_quote(self):
        """Незакрытая двойная кавычка - ошибка."""
        with self.assertRaises(ParseError):
            parse('ls "abc')

    def test_unclosed_single_quote(self):
        """Незакрытая одинарная кавычка - ошибка."""
        with self.assertRaises(ParseError):
            parse("ls 'abc")

    def test_trailing_escape(self):
        """Обратный слеш в конце строки - ошибка."""
        with self.assertRaises(ParseError):
            parse("ls abc\\")


if __name__ == "__main__":
    unittest.main()
