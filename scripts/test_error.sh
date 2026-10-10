#!/bin/sh
# Запуск эмулятора со скриптом, который останавливается на ошибке.
cd "$(dirname "$0")/.." || exit 1
sh run.sh --vfs vfs/files.json --script scripts/start_error.txt < /dev/null
echo "Код завершения: $?"
