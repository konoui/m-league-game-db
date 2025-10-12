#!/bin/bash

cd "$(dirname "$0")/.."

{
    echo "# SQL クエリ例"
    echo
    for file in query-examples/*.md; do
        basename="${file##*/}"
        [ "$basename" = "README.md" ] && continue
        name="${basename%.md}"
        echo "- [$name](./$basename)"
    done
} > query-examples/README.md
