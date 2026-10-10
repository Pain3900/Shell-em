#!/bin/sh
# Разные комбинации параметров командной строки.
cd "$(dirname "$0")/.." || exit 1
echo "=== Без параметров ==="
sh run.sh < /dev/null
echo "=== Только --vfs ==="
sh run.sh --vfs vfs/minimal.json < /dev/null
echo "=== Несуществующий стартовый скрипт ==="
sh run.sh --vfs vfs/files.json --script scripts/no_such_file.txt < /dev/null
echo "=== Неизвестный параметр ==="
sh run.sh --unknown < /dev/null
echo "Код завершения: $?"
