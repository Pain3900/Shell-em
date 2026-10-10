#!/bin/sh
# Минимальная VFS: пустой корневой каталог, без motd.
cd "$(dirname "$0")/.." || exit 1
sh run.sh --vfs vfs/minimal.json --script scripts/start_vfs.txt < /dev/null
echo "Код завершения: $?"
