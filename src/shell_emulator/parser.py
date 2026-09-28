"""Разбор командной строки на токены с поддержкой кавычек.

Правила разбора повторяют основные правила POSIX-оболочки:

* токены разделяются пробельными символами;
* в одинарных кавычках все символы берутся буквально;
* в двойных кавычках обратный слеш экранирует только ``"`` и ``\\``;
* вне кавычек обратный слеш экранирует любой следующий символ;
* кавычки могут стоять внутри слова: ``a"b c"d`` даёт ``ab cd``;
* пустые кавычки ``""`` дают пустой аргумент.
"""

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
ESCAPE = "\\"
ESCAPABLE_IN_DOUBLE = (DOUBLE_QUOTE, ESCAPE)


class ParseError(Exception):
    """Синтаксическая ошибка в командной строке."""


class _Tokenizer:
    """Посимвольный разборщик одной командной строки."""

    def __init__(self, line):
        """Подготовить разбор строки ``line``."""
        self.line = line
        self.pos = 0
        self.tokens = []
        self.buffer = []
        self.has_token = False

    def run(self):
        """Разобрать всю строку и вернуть список токенов."""
        while not self._at_end():
            self._feed(self._take())
        self._flush()
        return self.tokens

    def _at_end(self):
        """Проверить, достигнут ли конец строки."""
        return self.pos >= len(self.line)

    def _take(self):
        """Вернуть текущий символ и сдвинуться вперёд."""
        char = self.line[self.pos]
        self.pos += 1
        return char

    def _feed(self, char):
        """Обработать один символ вне кавычек."""
        if char.isspace():
            self._flush()
        elif char == SINGLE_QUOTE:
            self._read_single_quoted()
        elif char == DOUBLE_QUOTE:
            self._read_double_quoted()
        elif char == ESCAPE:
            self._read_escaped()
        else:
            self._add(char)

    def _add(self, char):
        """Добавить символ к текущему токену."""
        self.buffer.append(char)
        self.has_token = True

    def _flush(self):
        """Завершить текущий токен, если он начат."""
        if self.has_token:
            self.tokens.append("".join(self.buffer))
        self.buffer = []
        self.has_token = False

    def _read_escaped(self):
        """Прочитать символ после обратного слеша вне кавычек."""
        if self._at_end():
            raise ParseError("unexpected end of line after '\\'")
        self._add(self._take())

    def _read_single_quoted(self):
        """Прочитать содержимое одинарных кавычек (буквально)."""
        self.has_token = True
        end = self.line.find(SINGLE_QUOTE, self.pos)
        if end < 0:
            raise ParseError("unexpected EOF while looking for matching '")
        self.buffer.append(self.line[self.pos:end])
        self.pos = end + len(SINGLE_QUOTE)

    def _read_double_quoted(self):
        """Прочитать содержимое двойных кавычек."""
        self.has_token = True
        while not self._at_end():
            char = self._take()
            if char == DOUBLE_QUOTE:
                return
            if char == ESCAPE and not self._at_end():
                char = self._escaped_in_double()
            self.buffer.append(char)
        raise ParseError('unexpected EOF while looking for matching "')

    def _escaped_in_double(self):
        """Обработать обратный слеш внутри двойных кавычек."""
        if self.line[self.pos] in ESCAPABLE_IN_DOUBLE:
            return self._take()
        return ESCAPE


def parse(line):
    """Разбить командную строку на список аргументов.

    Args:
        line: строка, введённая пользователем.

    Returns:
        Список токенов; первый токен - имя команды.

    Raises:
        ParseError: если кавычка не закрыта или строка
            заканчивается обратным слешем.
    """
    return _Tokenizer(line).run()
