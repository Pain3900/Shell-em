#!/bin/sh
# VFS с несколькими файлами в корне, включая motd и двоичный файл.
cd "$(dirname "$0")/.." || exit 1
sh run.sh --vfs vfs/files.json --script scripts/start_vfs.txt < /dev/null
echo "Код завершения: $?"
