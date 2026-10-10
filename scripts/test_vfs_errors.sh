#!/bin/sh
# Ошибки загрузки VFS: эмулятор сообщает об ошибке и завершается с кодом 1.
cd "$(dirname "$0")/.." || exit 1
for vfs in vfs/no_such_file.json vfs/broken.json vfs/bad_type.json \
           vfs/bad_base64.json; do
    echo "=== $vfs ==="
    sh run.sh --vfs "$vfs" < /dev/null
    echo "Код завершения: $?"
done
