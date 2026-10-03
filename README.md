# Эмулятор командной оболочки UNIX (вариант 15)

Практическая работа №1 по дисциплине «Конфигурационное управление».
Консольное приложение (CLI) на Python, имитирующее работу командной
строки UNIX-подобной ОС.

## Общее описание

Текущий этап — **Этап 1. REPL**: минимальный прототип оболочки.

- Приглашение к вводу строится по реальным данным ОС:
  `username@hostname:~$`.
- Парсер корректно обрабатывает аргументы в кавычках.
- Команды `ls` и `cd` — заглушки: выводят своё имя и аргументы.
- Команда `exit` завершает работу эмулятора.

## Структура проекта

```
src/shell_emulator/
    __main__.py   точка входа (python -m shell_emulator)
    shell.py      класс Shell: приглашение, цикл REPL, выполнение строки
    parser.py     разбор строки на аргументы с учётом кавычек
    commands.py   встроенные команды (ls, cd, exit)
tests/            модульные тесты (unittest)
run.sh, run.bat   запуск эмулятора
test.sh, test.bat запуск тестов
```

## Функции и настройки

### Приглашение

`user@host:cwd$ `, где `user` — имя пользователя ОС (`getpass`),
`host` — имя компьютера до первой точки (`socket.gethostname`),
`cwd` — текущий каталог (на этом этапе всегда `~`).

### Парсер (`parser.parse`)

| Ввод                  | Результат              |
|-----------------------|------------------------|
| `ls  -l   /tmp`       | `['ls', '-l', '/tmp']` |
| `cd "My Documents"`   | `['cd', 'My Documents']` |
| `ls 'a "b" \c'`       | `['ls', 'a "b" \\c']`  |
| `ls a"b c"d`          | `['ls', 'ab cd']`      |
| `ls ""`               | `['ls', '']`           |
| `cd My\ Dir`          | `['cd', 'My Dir']`     |
| `ls "abc`             | ошибка: кавычка не закрыта |

Правила: в одинарных кавычках всё буквально; в двойных кавычках `\`
экранирует только `"` и `\`; вне кавычек `\` экранирует любой символ.

### Команды

| Команда      | Описание |
|--------------|----------|
| `ls [арг…]`  | заглушка, выводит `ls: args=[...]` |
| `cd [арг…]`  | заглушка, выводит `cd: args=[...]` |
| `exit [код]` | выход с кодом (по умолчанию 0) |

Ошибки: неизвестная команда (`command not found`), незакрытая кавычка
(`syntax error`), `exit abc` (`numeric argument required`),
`exit 1 2` (`too many arguments`). `Ctrl+D` завершает работу,
`Ctrl+C` сбрасывает текущий ввод, стрелки листают историю.

## Сборка и запуск

Требуется Python 3.8+, сторонние библиотеки не нужны.

```sh
./run.sh          # Linux / macOS
run.bat           # Windows
```

Запуск тестов:

```sh
./test.sh         # Linux / macOS
test.bat          # Windows
```

## Пример использования

```
student@laptop:~$ ls -l "My Documents"
ls: args=['-l', 'My Documents']
student@laptop:~$ cd 'a b' c\ d
cd: args=['a b', 'c d']
student@laptop:~$ ls "unclosed
shell: syntax error: unexpected EOF while looking for matching "
student@laptop:~$ foo
shell: foo: command not found
student@laptop:~$ exit abc
shell: exit: abc: numeric argument required
student@laptop:~$ exit 7
```
