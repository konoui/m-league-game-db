---
name: create-query
description: M リーグ試合データベースの SQL クエリ例を queries/ に新しく作る。GitHub Issue 番号や分析したい内容が与えられたとき、またはテーマ未指定で新しい分析クエリを考えてほしいと頼まれたときに使う。
---

# クエリ作成

`queries/<description>/` に `query.sql` と `meta.json` を作り、検証を通し、公開用の Markdown を生成するまでを行う。

## 参照するもの

- `references/query-format.md`: ファイル形式・命名・品質基準。**作成前に必ず読む**
- `references/analysis-perspectives.md`: 指標の定義と分析観点
- `TABLE.md`: テーブル定義。スキーマは `sqlite3 -readonly database.sqlite3 ".schema <table>"` でも確認できる
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

`description` を `references/query-format.md` の命名規則に従って決め、`queries/<description>/PLAN.md` に次の形式で計画を書く。内容をユーザーに提示し、**承認を得るまで `query.sql` と `meta.json` は作らない**。

```markdown
# {description}

- Issue: #{番号}（Issue がなければこの行を削除）

## 要件

{要件の要約。Issue に本文がない場合など、補って解釈した点も書く}

## 分析観点

{麻雀・M リーグの知識での解釈と、使う指標の定義}

## 使用テーブル・カラム

- {テーブル名}: {使用カラムとその役割}

## クエリ方針

{結合、集計の順序、絞り込み条件、並び順}

## 結果の不変条件

{一意になる粒度、値域、部分 ≤ 全体、内訳の合計など。meta.json の checks の元になる}

## 類似クエリ

- {既存の類似クエリ。なければ「なし」}
```

- 定義があいまいな場合（例: 「仕掛け」に暗槓を含むか）は、ここでユーザーに確認する。データを実際に引いて件数や分布を確かめ、定義による差を数字で示すと判断しやすい
- 指摘を受けたら `PLAN.md` を更新して再度提示する
- `PLAN.md` だけの段階では、Stop hook も `render.py` もこのディレクトリを検証しない

### 4. 作成する

1. `queries/<description>/query.sql` を書く
2. `queries/<description>/meta.json` を書く。`tables` は空配列のままにせず、分かる範囲で書いておく
3. `checks` を書く。`PLAN.md` の「結果の不変条件」を条件式にする。結果を見てから合わせにいくのではなく、SQL を実行する前に書く

`meta.json` があるクエリのファイルを保存するたびに、PostToolUse hook が `scripts/validate.py` を実行する。エラーが返ってきたら修正する。作業を終えるときは Stop hook が、変更したクエリの検証と `query-examples/` の生成漏れを確認する。

### 5. 検証する

```bash
uv run scripts/validate.py --fix queries/<description>
```

- `--fix` は `tables` を実際の参照テーブルに合わせて書き換える
- PASS するまで修正を繰り返す
- `checks` の違反は、まず SQL の誤りを疑う。ルールを緩めるのは、ルール自体がドメイン上誤っていると説明できる場合だけにする

`checks` で検出できるのは、書いた性質が破れる誤りだけ。**結果が正しいかは自分でも確かめる**:

```bash
sqlite3 -readonly -header -column database.sqlite3 < "queries/<description>/query.sql" | head -30
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

`PLAN.md` の末尾に次の節を追記し、計画から変わった点と、手順 5 で確かめた内容を記録する。

```markdown
## 検証結果

- {計画から変更した点とその理由}
- {結果の確認内容。例: 別方式で集計した値と全行一致、件数、実行時間}
```

作成したクエリの概要、検証結果、確認した結果の例をユーザーに伝える。
