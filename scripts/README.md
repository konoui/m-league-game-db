# scripts

## validate.py

`queries/<description>/` の `query.sql` と `meta.json` を検証する。

```bash
# 全件（database.sqlite3 で SQL も実行する）
uv run scripts/validate.py

# 指定したクエリのみ。--fix で meta.json の tables を実際の参照テーブルに書き換える
uv run scripts/validate.py --fix "queries/<description>"

# SQL を実行せず、形式だけ検証する
uv run scripts/validate.py --no-run
```

検証内容:

- `meta.json` が `schema/meta.schema.json` に合っているか
- ディレクトリ名と `description` が一致し、命名規則に従っているか
- `plan` に SQL の構文や識別子が含まれていないか
- `query.sql` の末尾の `;`、コメント（CTE の直前など）
- SQL が読み取り専用の 1 文で、エラーなく 1 行以上返すか
- `tables` が SQL の実際の参照テーブル（SQLite の authorizer で取得）と一致するか

## render.py

`queries/` から `query-examples/*.md` と `query-examples/README.md` を生成する。`--check` を付けると書き込まず、生成物が最新かどうかだけを確認する（CI で使用）。

```bash
uv run scripts/render.py
```

## make.sh

外部リポジトリからデータベースファイル・ドキュメントをコピーし、テーブル定義と `query-examples/` を再生成する。

### make-table-doc.py

`m-converter` の `table-doc.yaml` からテーブル定義ドキュメント `TABLE.md` を目次込みで生成する。
YAML が定義の正とし、表形式・目次のフォーマットはこのスクリプトが正。
make.sh から呼ばれる。

## total-records.sh

全てのテーブルの合計レコード数を出力するユーティリティ。

```bash
./scripts/total-records.sh database.sqlite3
9034370
```
