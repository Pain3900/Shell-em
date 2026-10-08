#!/bin/sh
# Запуск эмулятора с VFS и корректным стартовым скриптом.
cd "$(dirname "$0")/.." || exit 1
sh run.sh --vfs vfs/vfs.json --script scripts/start_ok.txt < /dev/null
echo "Код завершения: $?"
