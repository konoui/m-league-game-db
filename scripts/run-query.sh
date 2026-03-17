#!/bin/bash
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <db-file> <markdown-file>" >&2
  exit 1
fi

db="$1"
md="$2"
script_dir="$(cd "$(dirname "$0")" && pwd)"

sql=$("$script_dir/extract-sql.sh" "$md") || exit 1

result=$(sqlite3 "$db" "$sql") || {
  echo "FAIL: $md (query execution error)" >&2
  exit 1
}

row_count=$(printf '%s\n' "$result" | grep -c .)

if [ "$row_count" -eq 0 ]; then
  echo "FAIL: $md (0 rows returned)" >&2
  exit 1
fi

echo "PASS: $md ($row_count rows)"
