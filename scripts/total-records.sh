#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage:" >&2
  echo "  $0 specify db file" >&2
  exit 1
}


[ $# -lt 1 ] && usage

DB=$1
INNER=$(sqlite3 "$DB" "SELECT GROUP_CONCAT('SELECT COUNT(*) cnt FROM ' || name, ' UNION ALL ') FROM sqlite_master WHERE type='table' AND name
NOT LIKE 'sqlite_%';")
sqlite3 "$DB" "SELECT SUM(cnt) FROM ($INNER);"
