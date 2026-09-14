---
name: create-query
description: M リーグ試合データベースの SQL クエリ例を queries/ に新しく作る。GitHub Issue 番号や分析したい内容が与えられたとき、またはテーマ未指定で新しい分析クエリを考えてほしいと頼まれたときに使う。
---

# クエリ作成

`queries/<description>/` に `query.sql` と `meta.json` を作り、検証を通し、公開用の Markdown を生成するまでを行う。

## 参照するもの

- `references/query-format.md`: ファイル形式・命名・品質基準。**作成前に必ず読む**
- `references/analysis-perspectives.md`: 指標の定義と分析観点
- `TABLE.md`: テーブル定義。スキーマは `sqlite3 database.sqlite3 ".schema <table>"` でも確認できる
- `PAI_FORMAT.md`（牌の表し方）、`YAKU_NAMES.md`（役名）、`MLEAGUE.md`（M リーグの情報。あれば読む）
- 既存の `queries/*/`: 同じ結合・集計パターンを探す手本

## 手順

### 1. 要件を把握する

- Issue 番号が与えられた場合は `gh issue view <番号>` で内容を取得する
- 分析内容が与えられた場合はそれを要件とする
- テーマが未指定の場合は `references/analysis-perspectives.md` を基に、既存クエリにない切り口を 3 案ほど出してユーザーに選んでもらう。時間軸・対象軸・統計軸のうち 3 つ以上を組み合わせたもの、指標どうしの比較・相関を見るもの、具体的な問いに答えるものを優先する

### 2. 既存クエリを調べる

- `ls queries/` と `grep -l <キーワード> queries/*/meta.json` で類似クエリを探す
- 同じ内容のクエリがあれば、新しく作らずにユーザーへ報告する
- 類似クエリがあれば、その結合方法・チーム所属の絞り込み・並び順を踏襲する

### 3. 計画を立て、承認を得る

次の内容をユーザーに提示し、承認を得てから作成に進む。

- 要件の要約
- 分析観点（麻雀・M リーグの知識での解釈と、指標の定義）
- 使用するテーブルと、各カラムの役割
- クエリの方針（結合、集計の順序、絞り込み条件、並び順）
- 類似クエリ

定義があいまいな場合（例: 「仕掛け」に暗槓を含むか）は、ここでユーザーに確認する。データを実際に引いて件数や分布を確かめ、定義による差を数字で示すと判断しやすい。

### 4. 作成する

1. `description` を `references/query-format.md` の命名規則に従って決める
2. `queries/<description>/query.sql` を書く
3. `queries/<description>/meta.json` を書く。`tables` は空配列のままにせず、分かる範囲で書いておく

ファイルを保存するたびに PostToolUse hook が `scripts/validate.py` を実行する。エラーが返ってきたら修正する。`query.sql` を書いた直後は `meta.json` がまだないためエラーになるが、これは想定どおり。

### 5. 検証する

```bash
uv run scripts/validate.py --fix queries/<description>
```

- `--fix` は `tables` を実際の参照テーブルに合わせて書き換える
- PASS するまで修正を繰り返す

validate は形式と実行可否しか見ない。**結果が正しいかは自分で確かめる**:

```bash
sqlite3 -header -column database.sqlite3 < "queries/<description>/query.sql" | head -30
```

- 件数・値の範囲が常識的か（例: 率が 0〜100 に収まる、試合数がシーズンの総試合数を超えない）
- JOIN で行が重複して、回数が水増しされていないか
- 可能なら別の方法で集計した値と突き合わせる

### 6. 公開用 Markdown を生成する

```bash
uv run scripts/render.py
```

`query-examples/<description>.md` と `query-examples/README.md` が更新される。

### 7. 報告する

作成したクエリの概要、検証結果、確認した結果の例をユーザーに伝える。PR を作る場合は、手順 3 の計画と手順 5 で確かめた内容を PR 本文に書く（リポジトリには計画ファイルを残さない）。
