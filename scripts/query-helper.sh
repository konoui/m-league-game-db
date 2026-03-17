#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage:" >&2
  echo "  $0 extract <markdown-file>" >&2
  echo "  $0 run <db-file> <markdown-file>" >&2
  echo "  $0 run-all <db-file> <query-examples-dir>" >&2
  exit 1
}

extract_sql() {
  local md="$1"
  local sql
  sql=$(awk '/^```sql$/{ found=1; next } found && /^```$/{ exit } found{ print }' "$md")
  if [ -z "$sql" ]; then
    echo "Error: No sql code block found in $md" >&2
    exit 1
  fi
  printf '%s\n' "$sql"
}

run_query() {
  local db="$1" md="$2"
  local sql result row_count

  sql=$(extract_sql "$md") || exit 1

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
}

[ $# -lt 1 ] && usage

case "$1" in
  extract)
    [ $# -ne 2 ] && usage
    extract_sql "$2"
    ;;
  run)
    [ $# -ne 3 ] && usage
    run_query "$2" "$3"
    ;;
  run-all)
    [ $# -ne 3 ] && usage
    for f in "$3"/*.md; do
      [ "$(basename "$f")" = "README.md" ] && continue
      run_query "$2" "$f" || exit 1
    done
    ;;
  *)
    usage
    ;;
esac
