#!/bin/bash

# Get current date
DATE=$(date +%Y%m%d_%H%M%S)

# Export filename
DUMP_FILE="taurus_auth.dump.sql"
DATE_DUMP_FILE="taurus_auth.dump.${DATE}.sql"

# Execute export
/usr/bin/mysqldump --column-statistics=0 --skip-lock-tables --routines --add-drop-table --disable-keys --extended-insert -uroot -h 127.0.0.1 --port=3306 taurus_auth -p123456 > "${DATE_DUMP_FILE}"

# Create latest symlink (points to most recent export file)
ln -sf "${DATE_DUMP_FILE}" "${DUMP_FILE}"

echo "Export completed: ${DATE_DUMP_FILE}"
echo "Latest link updated: ${DUMP_FILE} -> ${DATE_DUMP_FILE}"