"""Графическое окно эмулятора на tkinter.

Окно состоит из области вывода, строки ввода команды и кнопки ``>``.
Выполнение команд делегируется классу :class:`Shell`.
"""

import tkinter as tk
from tkinter import font as tkfont

from shell_emulator.commands import ExitRequest
from shell_emulator.shell import Shell

WINDOW_SIZE = "760x480"
MIN_WIDTH = 400
MIN_HEIGHT = 250
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
PROMPT_COLOR = "#6a9955"
ERROR_COLOR = "#f44747"
INPUT_BG_COLOR = "#2d2d2d"
BORDER_COLOR = "#5a5a5a"
FONT_SIZE = 11
PADDING = 6
OUTPUT_TAG = "output"
ERROR_TAG = "error"
PROMPT_TAG = "prompt"


class TextWriter:
    """Поток вывода, который дописывает текст в виджет ``Text``."""

    def __init__(self, widget, tag):
        """Связать поток с виджетом ``widget`` и тегом оформления ``tag``."""
        self.widget = widget
        self.tag = tag

    def write(self, text):
        """Дописать ``text`` в конец области вывода."""
        self.widget.configure(state=tk.NORMAL)
        self.widget.insert(tk.END, text, self.tag)
        self.widget.configure(state=tk.DISABLED)
        self.widget.see(tk.END)

    def flush(self):
        """Ничего не делать: вывод в виджет не буферизуется."""


class ShellWindow:
    """Главное окно эмулятора: вывод, строка ``cmd`` и кнопка ``>``."""

    def __init__(self, root):
        """Построить интерфейс в корневом окне ``root``."""
        self.root = root
        self.exit_code = 0
        self.history = []
        self.history_pos = 0
        self.entry = self._build_input()
        self.output = self._build_output()
        self.shell = Shell(
            stdout=TextWriter(self.output, OUTPUT_TAG),
            stderr=TextWriter(self.output, ERROR_TAG),
        )
        self.prompt_writer = TextWriter(self.output, PROMPT_TAG)
        root.title(f"Эмулятор - {self.shell.user}@{self.shell.host}")
        root.geometry(WINDOW_SIZE)
        root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.entry.focus_set()

    def _mono_font(self):
        """Вернуть моноширинный шрифт для вывода и ввода."""
        family = tkfont.nametofont("TkFixedFont").actual("family")
        return (family, FONT_SIZE)

    def _build_output(self):
        """Создать область вывода с полосой прокрутки."""
        frame = tk.Frame(self.root)
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                   padx=PADDING, pady=PADDING)
        output = tk.Text(
            frame, bg=BG_COLOR, fg=FG_COLOR, font=self._mono_font(),
            wrap=tk.WORD, state=tk.DISABLED, borderwidth=0, height=1,
            highlightthickness=0,
        )
        scroll = tk.Scrollbar(frame, command=output.yview)
        output.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output.tag_configure(ERROR_TAG, foreground=ERROR_COLOR)
        output.tag_configure(PROMPT_TAG, foreground=PROMPT_COLOR)
        return output

    def _build_input(self):
        """Создать строку ввода команды и кнопку ``>``."""
        frame = tk.Frame(self.root)
        frame.pack(side=tk.BOTTOM, fill=tk.X,
                   padx=PADDING, pady=(0, PADDING))
        button = tk.Button(frame, text=">", width=3, command=self.submit)
        button.pack(side=tk.RIGHT, padx=(PADDING, 0))
        entry = tk.Entry(
            frame, font=self._mono_font(), bg=INPUT_BG_COLOR,
            fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT,
            highlightthickness=1, highlightbackground=BORDER_COLOR,
            highlightcolor=PROMPT_COLOR,
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind("<Return>", lambda _event: self.submit())
        entry.bind("<Up>", lambda _event: self._browse_history(-1))
        entry.bind("<Down>", lambda _event: self._browse_history(1))
        return entry

    def _browse_history(self, step):
        """Подставить в строку ввода предыдущую/следующую команду."""
        self.history_pos = max(0, min(len(self.history),
                                      self.history_pos + step))
        text = ""
        if self.history_pos < len(self.history):
            text = self.history[self.history_pos]
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def submit(self):
        """Выполнить команду из строки ввода и вывести результат."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        if line.strip():
            self.history.append(line)
        self.history_pos = len(self.history)
        self.prompt_writer.write(self.shell.prompt())
        self.shell.stdout.write(line + "\n")
        try:
            self.shell.execute(line)
        except ExitRequest as request:
            self.exit_code = request.code
            self.root.destroy()


def run_gui():
    """Открыть окно эмулятора и вернуть код завершения."""
    root = tk.Tk()
    window = ShellWindow(root)
    root.mainloop()
    return window.exit_code
