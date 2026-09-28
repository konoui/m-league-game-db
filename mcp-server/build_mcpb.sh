#!/usr/bin/env bash
# Claude Desktop の拡張機能（.mcpb）を dist/ に作る。
#   使い方: ./build_mcpb.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
VERSION="${VERSION:-0.1.0}"
BUILD="$HERE/build/mcpb"
DIST="$HERE/dist"

rm -rf "$BUILD" && mkdir -p "$BUILD/src/docs/queries" "$DIST"

# サーバー本体と、サーバーが読む文書・用語集・クエリ例
cp "$HERE/server.py" "$BUILD/src/server.py"
cp "$HERE/GLOSSARY.md" "$HERE/RECIPES.md" "$BUILD/src/docs/"
for f in TABLE.duckdb.md MLEAGUE.md DB_NAMING.md PAI_FORMAT.md YAKU_NAMES.md DB_CHANGELOG.md; do
  cp "$REPO/$f" "$BUILD/src/docs/"
done
for d in "$REPO"/queries/*/; do
  name="$(basename "$d")"
  mkdir -p "$BUILD/src/docs/queries/$name"
  cp "$d/meta.json" "$d/query.sql" "$BUILD/src/docs/queries/$name/"
done

cat > "$BUILD/pyproject.toml" <<EOF
[project]
name = "m-league-db"
version = "$VERSION"
requires-python = ">=3.11"
dependencies = ["mcp>=2,<3", "duckdb>=1.1", "httpx>=0.27"]
EOF

cat > "$BUILD/manifest.json" <<EOF
{
  "manifest_version": "0.4",
  "name": "m-league-db",
  "display_name": "M リーグ データベース",
  "version": "$VERSION",
  "description": "M リーグ（プロ麻雀リーグ）の全試合データに、日本語で質問できるようにします。",
  "long_description": "2018-19 シーズン以降の M リーグの試合・局・打牌のデータを、読み取り専用で検索します。データは初回に自動で取得し、以降は 1 日 1 回、新しい試合があれば自動で更新します。",
  "author": { "name": "m-league-game-db contributors" },
  "homepage": "https://github.com/konoui/m-league-game-db",
  "license": "MIT",
  "server": {
    "type": "uv",
    "entry_point": "src/server.py",
    "mcp_config": { "command": "uv", "args": ["run", "--directory", "\${__dirname}", "src/server.py"] }
  },
  "tools": [
    { "name": "run_sql", "description": "読み取り専用で SQL を実行する" },
    { "name": "list_tables", "description": "テーブル一覧と日本語の説明" },
    { "name": "describe_table", "description": "列の型と説明・注意書き" },
    { "name": "search_query_examples", "description": "検証済みのクエリ例から似たものを探す" },
    { "name": "find_player", "description": "選手を名前・ふりがなで探す" },
    { "name": "get_doc", "description": "用語集・ルール・牌の表記などの文書" },
    { "name": "database_info", "description": "データの期間と版" },
    { "name": "update_database", "description": "最新のデータに差し替える" }
  ],
  "compatibility": { "platforms": ["darwin", "win32", "linux"], "runtimes": { "python": ">=3.11" } }
}
EOF

(cd "$BUILD" && npx -y @anthropic-ai/mcpb validate manifest.json && npx -y @anthropic-ai/mcpb pack . "$DIST/m-league-db.mcpb")

echo "作成: $DIST/m-league-db.mcpb"
