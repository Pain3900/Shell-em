#!/bin/sh
# Этап 5: команды cp и chmod на VFS с вложенными каталогами.
# 1) Стартовый скрипт показывает все режимы команд.
# 2) Ошибки подаются на обычный ввод (как на этапе 4).
# 3) Повторный запуск показывает, что изменения были только в памяти:
#    VFS снова загружается в исходном виде.
cd "$(dirname "$0")/.." || exit 1
echo "=== Все режимы команд (стартовый скрипт) ==="
sh run.sh --vfs vfs/deep.json --script scripts/start_stage5.txt < /dev/null
echo
echo "=== Ошибки команд (ввод из файла) ==="
sh run.sh --vfs vfs/deep.json < scripts/stage5_errors.txt 2>&1
echo
echo "=== Повторный запуск: копий нет, права исходные ==="
printf 'ls -l /home/user\nls /etc\n' | sh run.sh --vfs vfs/deep.json
