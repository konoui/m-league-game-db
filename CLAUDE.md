# m-league-game-db

M リーグの試合情報 SQLite データベースの配布と、そのデータベースに対する SQL クエリ例を管理するリポジトリ。

## 構成

- `queries/<description>/`: クエリ例の正。`query.sql`（SQL 本体）と `meta.json`（description, plan, tables）
- `schema/meta.schema.json`: `meta.json` の JSON Schema
- `query-examples/`: `queries/` から生成する公開用 Markdown。**手で編集しない**
- `TABLE.md`, `PAI_FORMAT.md`, `YAKU_NAMES.md`: `scripts/make.sh` で外部リポジトリからコピー・生成する。直接編集しない
- `database.sqlite3`: `scripts/make.sh` でコピーするか、リリースからダウンロードする（git 管理外）

## クエリの作成・修正

- 新規作成: `create-query` skill
- 既存クエリの見直し: `review-query` skill
- 形式・命名・品質基準: `.claude/skills/create-query/references/query-format.md`

`queries/` 配下を編集すると、PostToolUse hook が `scripts/validate.py` を実行する。

## コマンド

```bash
uv run scripts/validate.py [--fix] [queries/<description> ...]  # 検証
uv run scripts/render.py [--check]                              # query-examples/ を生成
```

`queries/` を変更したら、コミット前に上の 2 つを実行する。CI（`.github/workflows/validate-queries.yml`）でも同じ内容を検査する。
