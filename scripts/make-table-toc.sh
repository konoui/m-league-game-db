#!/bin/bash

cd "$(dirname "$0")/.."

FILE="TABLE.md"
TOC_BEGIN="<!-- TOC BEGIN -->"
TOC_END="<!-- TOC END -->"

# Remove existing ToC (including surrounding blank line before it)
if grep -q "$TOC_BEGIN" "$FILE"; then
    begin=$(grep -n "$TOC_BEGIN" "$FILE" | head -1 | cut -d: -f1)
    end=$(grep -n "$TOC_END" "$FILE" | head -1 | cut -d: -f1)
    # Also remove one blank line before TOC_BEGIN if present
    if [ "$begin" -gt 1 ] && sed -n "$((begin - 1))p" "$FILE" | grep -q '^$'; then
        begin=$((begin - 1))
    fi
    {
        head -n "$((begin - 1))" "$FILE"
        tail -n "+$((end + 1))" "$FILE"
    } > "$FILE.tmp" && mv "$FILE.tmp" "$FILE"
fi

# Generate ToC from headings (## and deeper)
toc_file=$(mktemp)
{
    echo "$TOC_BEGIN"
    echo
    while IFS= read -r line; do
        if [[ "$line" =~ ^(#{2,})\ (.+) ]]; then
            hashes="${BASH_REMATCH[1]}"
            title="${BASH_REMATCH[2]}"
            depth=$(( ${#hashes} - 2 ))
            indent=$(printf '%*s' $((depth * 2)) '')
            anchor=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g; s/[^a-z0-9ぁ-んァ-ヶー一-龠々\-]//g')
            echo "${indent}- [${title}](#${anchor})"
        fi
    done < "$FILE"
    echo
    echo "$TOC_END"
} > "$toc_file"

# Insert ToC after the first # heading line
first_heading_line=$(grep -n '^# ' "$FILE" | head -1 | cut -d: -f1)
if [ -n "$first_heading_line" ]; then
    {
        head -n "$first_heading_line" "$FILE"
        echo
        cat "$toc_file"
        tail -n +"$((first_heading_line + 1))" "$FILE"
    } > "$FILE.tmp" && mv "$FILE.tmp" "$FILE"
fi

rm -f "$toc_file"
