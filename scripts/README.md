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
- 結果が `checks` の不変条件（一意キー、行数、行ごとの条件式）を満たすか

## render.py

`queries/` から `query-examples/*.md` と `query-examples/README.md` を生成する。`--check` を付けると書き込まず、生成物が最新かどうかだけを確認する（CI で使用）。

```bash
uv run scripts/render.py
```

## make.sh

ローカル作業用に、外部リポジトリから同期できないものだけを用意する。

- `database.sqlite3`: m-converter が作った DB をコピーする
- `MLEAGUE.md`: 非公開のためワークフローでは配布できない
- `query-examples/`: `render.py` で再生成する

`TABLE.sqlite3.md` / `TABLE.duckdb.md` / `DB_CHANGELOG.md` / `DB_NAMING.md` / `YAKU_NAMES.md` / `PAI_FORMAT.md` は
m-league-score-sheet の sync-db-docs ワークフローが main へ push するので、make.sh では扱わない。
古い checkout から生成すると同期済みの内容を巻き戻してしまうため。
ローカルで生成物を確認したいときは m-converter 側の `scripts/make-table-doc.py` を直接実行する。

## validate-duckdb.py

`queries/` の SQL が DuckDB 版のデータベースでも実行できるか検証する。
SQLite 版の検証は validate.py が行い、こちらは DuckDB 固有の差だけを見る。

```bash
uv run scripts/validate-duckdb.py [--db FILE] [queries/<description> ...]
```

つまずきやすいのは次の 2 つ。

- **GROUP BY**: SQLite は GROUP BY にない列の select を許すが、DuckDB は許さない。
  グループを一意に決める列（`p.id` で束ねているときの `p.name` など）を GROUP BY に足す。
  SQLite の結果は変わらない
- **関数の差**: `strftime` は引数の順が逆。`date` は `YYYY-MM-DD` の文字列なので、
  `substr(date, 1, 4)` のようにどちらでも同じ意味になる書き方にする

## snapshot.py

`queries/<description>/result.json`（固定した版の DB での実行結果）を検査・更新する。
クエリを書き換えたときに結果が変わったかどうかを、`result.json` の差分として見えるようにするためのもの。

```bash
# 全件を検査する（result.json と一致しなければ失敗し、差分を表示する）
uv run scripts/snapshot.py

# 指定したクエリの result.json を作り直す（DB の版はそのまま）
uv run scripts/snapshot.py --update "queries/<description>"

# DB の版を最新のリリースに進めて作り直す
uv run scripts/snapshot.py --update --release latest "queries/<description>"
```

- DB は日々更新されるので、結果は `result.json` の `db` に書いたリリース（DuckDB 版）で固定する。新しく作るクエリは最新のリリースになる
- そのリリースの DB は初回に `gh release download` で取得し、`.cache/snapshot-db/<タグ>/` に置く（`gh` が必要）
- `validate.py` は最新の DB で不変条件が成り立つかを見る。こちらは同じ DB で結果が変わっていないかを見る。最初から誤っている結果は検出できない
- 固定した版の DB でクエリが動かなくなったとき（スキーマの変更に追従したとき）は、`--release latest` で版を進める
- 結果が実行のたびに変わらないよう、クエリの最終結果の並び順は、同じ値の行の順序まで決めておく

## total-records.sh

全てのテーブルの合計レコード数を出力するユーティリティ。

```bash
./scripts/total-records.sh database.sqlite3
9034370
```
