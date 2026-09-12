# scripts

## make.sh

外部リポジトリからデータベースファイル・クエリ例をコピーし、テーブル定義・目次・README を再生成する。

### make-table-doc.py

`m-converter` の `table-doc.yaml` からテーブル定義ドキュメント `TABLE.md` を目次込みで生成する。
YAML が定義の正とし、表形式・目次のフォーマットはこのスクリプトが正。
make.sh から呼ばれる。

### make-query-readme.sh

`query-examples/` 内の Markdown ファイル一覧から `query-examples/README.md` を自動生成する。
make.sh から呼ばれる。

## release.sh

`database.sqlite3` を zip 圧縮し、`gh release create` で GitHub リリースを作成する。
テスト目的での使用を想定している。

## query-helper.sh

Markdown ファイル内の SQL クエリの抽出・実行・検証を行うユーティリティ。

```bash
# SQL 抽出のみ
./scripts/query-helper.sh extract <markdown-file>

# 単一ファイルの実行・検証
./scripts/query-helper.sh run <db-file> <markdown-file>

# 全ファイルの実行・検証（README.md は自動スキップ）
./scripts/query-helper.sh run-all <db-file> <query-examples-dir>
```

## total-records.sh

全てのテーブルの合計レコード数を出力するユーティリティ。

```bash
./scripts/total-records.sh database.sqlite3
9034370
```
