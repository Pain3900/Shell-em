#!/bin/sh
# VFS с вложенными каталогами (6 уровней) и motd.
cd "$(dirname "$0")/.." || exit 1
sh run.sh --vfs vfs/deep.json --script scripts/start_vfs.txt < /dev/null
echo "Код завершения: $?"
