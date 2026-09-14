#!/bin/bash

(
    converter=./../m-league-score-sheet/m-converter
    cp "$converter/data/database.db" ./database.sqlite3
    uv run --quiet --with pyyaml python ./scripts/make-table-doc.py "$converter/table-doc.yaml" ./TABLE.md
    cp "$converter/YAKU_NAMES.md" ./YAKU_NAMES.md
    cp "$converter/PAI_FORMAT.md" ./PAI_FORMAT.md
    # クエリ作成時に参照する M リーグの情報（公開しない）
    cp ./../konoui.dev/m-ai-cat/agent/MLEAGUE.md ./MLEAGUE.md
    uv run ./scripts/render.py
)
