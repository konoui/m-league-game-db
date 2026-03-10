#!/usr/bin/env python3
import re
import sys
import unicodedata

FILE = "TABLE.md"
TOC_BEGIN = "<!-- TOC BEGIN -->"
TOC_END = "<!-- TOC END -->"


def slugify(text):
    """Generate GitHub-compatible heading anchor."""
    s = text.lower()
    # Replace spaces with hyphens
    s = s.replace(" ", "-")
    # Keep: alphanumeric (including unicode letters/numbers), hyphens, underscores
    result = []
    for ch in s:
        if ch in ("-", "_"):
            result.append(ch)
        elif unicodedata.category(ch).startswith(("L", "N")):
            result.append(ch)
    return "".join(result)


def main():
    with open(FILE, "r") as f:
        lines = f.readlines()

    # Remove existing ToC block (and one blank line before it)
    begin_idx = end_idx = None
    for i, line in enumerate(lines):
        if TOC_BEGIN in line and begin_idx is None:
            begin_idx = i
        if TOC_END in line:
            end_idx = i
    if begin_idx is not None and end_idx is not None:
        # Remove blank line before TOC_BEGIN if present
        if begin_idx > 0 and lines[begin_idx - 1].strip() == "":
            begin_idx -= 1
        lines = lines[:begin_idx] + lines[end_idx + 1 :]

    # Generate ToC from ## and deeper headings
    toc_lines = [TOC_BEGIN + "\n", "\n"]
    for line in lines:
        m = re.match(r"^(#{2,})\s+(.+)", line)
        if m:
            depth = len(m.group(1)) - 2
            title = m.group(2).strip()
            anchor = slugify(title)
            indent = "  " * depth
            toc_lines.append(f"{indent}- [{title}](#{anchor})\n")
    toc_lines.append("\n")
    toc_lines.append(TOC_END + "\n")

    # Insert ToC after the first # heading
    for i, line in enumerate(lines):
        if re.match(r"^# ", line):
            lines = lines[: i + 1] + ["\n"] + toc_lines + lines[i + 1 :]
            break

    with open(FILE, "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    main()
