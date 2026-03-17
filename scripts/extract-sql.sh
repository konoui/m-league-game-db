#!/bin/bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <markdown-file>" >&2
  exit 1
fi

sql=$(awk '/^```sql$/{ found=1; next } found && /^```$/{ exit } found{ print }' "$1")

if [ -z "$sql" ]; then
  echo "Error: No sql code block found in $1" >&2
  exit 1
fi

printf '%s\n' "$sql"
