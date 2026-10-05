# クエリの形式と品質基準

`scripts/validate.py check` が機械的に検査するルールには「(validate)」を付けています。付いていないルールは検査されないため、作成者やレビュー担当が確認してください。

## ディレクトリ構成

```
queries/<description>/
  PLAN.md     # 作成時の計画と検証の記録（公開用 Markdown には含めない）
  query.sql   # SQL 本体
  meta.json   # description, plan, tables, checks（schema/meta.schema.json）
  result.json # 固定した版の DB での実行結果（validate.py update-result が作る）
```

- ディレクトリ名は `description` と完全に一致させる (validate)
- 置けるファイルは `query.sql`、`meta.json`（必須）と `PLAN.md`、`result.json`（任意）だけ (validate)
- `result.json` は `uv run scripts/validate.py update-result` で作る。手で編集しない (validate)
- `query-examples/*.md` は `uv run scripts/render.py` で生成するため、手で編集しない (CI)

## meta.json

```json
{
  "description": "シーズン・ステージ別のプレイヤー別先制リーチ率を算出するクエリ",
  "plan": [
    "各局で最初にリーチしたプレイヤーを特定し、プレイヤーごとに先制リーチをどれだけ打てているかを明らかにする",
    "先制リーチは局内で最初に成立したリーチとする",
    "まず局単位でリーチの順番を求め、次にシーズン・ステージ・プレイヤー単位で集計する",
    "結果はシーズン降順、ステージ順、先制リーチ率の降順で並べる"
  ],
  "tables": ["reach_event", "event", "player", "kyoku", "game", "season_stage", "league_season", "game_player_result", "team"],
  "checks": {
    "unique": ["シーズン", "ステージ", "プレイヤー名"],
    "rules": ["先制リーチ回数 BETWEEN 0 AND リーチ回数", "先制リーチ率 BETWEEN 0 AND 100"]
  }
}
```

### description

形式: `[分析単位][対象別][記録・統計内容][範囲・条件][処理内容]クエリ` (validate)

| 要素 | 選択肢 |
|---|---|
| 分析単位 | `シーズン・ステージ別の` / `シーズン別の` / `ステージ別の` / `暦年別の` / `全期間の` |
| 対象 | `プレイヤー別` / `チーム別` / `試合別` / `席別`（「プレイヤーごと」ではなく必ず「〜別」） |
| 記録・統計内容 | 連続○着記録 / ○○統計 / ○○回数 / ○○率 など |
| 範囲・条件 | 上位○件 / ○○超え / ○順目 / なし |
| 処理内容 | `を算出する` / `を取得する` / `を分析する` |

表記ルール:

- 順位は「着」で書く: 1位 → 1着 (validate)
- 複合条件: 連対（1着または2着）、逆連対（3着または4着）
- 配牌時は `0順目（配牌時）` と書く (validate)
- 英字は使わない: query → クエリ、analysis → 分析 (validate)
- 80 文字以内、`/\:*?"<>|` は使わない (validate)
- **取得系の省略**: 処理内容が `を取得する` のときは、記録・統計内容を具体的に書きすぎない（例:「〜の年・対局日」）。`基本情報` / `試合情報` / `統計情報` / `詳細情報` のいずれかにまとめる

良い例:

- `シーズン・ステージ別のプレイヤー別連続4着回数上位10件を算出するクエリ`
- `全期間のプレイヤー別100ポイント超え基本情報を取得するクエリ`

悪い例:

- `連続4着回数` → 分析単位・対象・処理内容がない
- `シーズン別のプレイヤーごとの1位回数を算出するクエリ` → 「ごと」「1位」

### plan

文字列の配列で、1 要素に 1 項目を書く。先頭に `- ` などの記号は付けない (validate)

次の観点を含める:

1. **目的**: この分析で何を明らかにしたいか
2. **指標定義**: 使う指標の意味（ドメイン知識を含む。例: 先制リーチ = 局内で最初に成立したリーチ）
3. **設計方針**: データをどの順で加工するか（例: まず局単位でリーチの順番を求め、次にプレイヤー単位で集計する）
4. **出力方針**: 並び順・件数制限・表示形式の意図

SQL の構文、テーブル名、カラム名、CTE 名は書かない。すべて自然言語で説明する（検索での精度を保つため）(validate: snake_case の識別子と主な SQL 用語を検出)

### tables

SQL が参照するテーブル・ビューを列挙する。`uv run scripts/validate.py check --fix <dir>` を実行すると、実際に参照しているテーブルに合わせて自動で書き換わる (validate)

### checks

クエリ結果が満たすべき不変条件。validate がクエリを実行し、結果の全行に対して検査する (validate)

```json
"checks": {
  "unique": ["シーズン", "ステージ", "プレイヤー名"],
  "rows": {"max": 10},
  "rules": [
    "ステージ IN ('regular', 'semifinal', 'final')",
    "プレイヤー名 IS NOT NULL",
    "先制リーチ回数 BETWEEN 0 AND リーチ回数",
    "先制リーチ率 BETWEEN 0 AND 100"
  ]
}
```

| キー | 必須 | 内容 |
|---|---|---|
| `unique` | ○ | 結果の 1 行を一意に特定する出力カラムの組。集計の粒度を表す |
| `rules` | ○ | 全行で真になる SQLite の条件式。出力カラム名で参照する |
| `rows` | | 結果の行数の範囲（`min` / `max`）。「上位 10 件」なら `{"max": 10}` |

**現在のデータからではなく、ドメイン上必ず成り立つ性質を書く。** DB が更新されても成り立ち、クエリの誤りで破れる条件がよい。

- **粒度**: `unique` は description の「〜別」と一致させる。結合で行が増える誤りを検出できる。`unique` に書く列の組が、件数を絞った結果だけでなく元のデータでも一意か、重複を数えるクエリで確かめる
- **値域**: 率は `BETWEEN 0 AND 100`、平均順位は `BETWEEN 1 AND 4`、回数は `>= 0`
- **包含関係**: 部分の回数 ≤ 全体の回数（例: `先制リーチ回数 <= リーチ回数`、`first_place_count <= rentai_count`）
- **合計の整合**: 内訳の合計 = 全体（例: `一着回数 + 二着回数 + 三着回数 + 四着回数 = 総ゲーム数`）。丸めた値は `ABS(... - 100) <= 0.1` のように誤差を許す
- **導出の整合**: 別カラムから再計算した値と一致する（例: `記録終了局順 - 記録開始局順 + 1 = 連続あがり回数`）
- **数え直しとの一致**: 中心となる集計が誤ると破れるルールを、少なくとも 1 つ入れる。値域や形式のルールだけでは、数え方の誤りを検出できない。別の方法で数え直した値を出力に加え、一致を条件にする（例: `期間内出場試合数 = 連続1着回避回数`）
- **形式**: `シーズン GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]'`、日付の `GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'`

注意:

- 式が NULL になる行は違反とみなされない。NULL を許さないカラムには `IS NOT NULL` を書く
- 数字で始まるカラム名はダブルクォートで囲む（例: `"1着獲得回数" >= 1`）。存在しないカラム名はエラーになる
- `;` は使えない

## result.json

クエリを書き換えたときに結果が変わったかどうかを、差分として見えるようにするためのファイル。DB は日々更新されるので、特定のリリースの DB（DuckDB 版）での実行結果を保存する。`db` にそのリリースのタグ、`columns` に出力カラム、`rows` に結果を 1 行ずつ持つ。

- 検査: `uv run scripts/validate.py check [queries/<description> ...]`。保存した結果と一致しなければ失敗する (validate)
- 作り直し: `uv run scripts/validate.py update-result queries/<description>`。DB の版は変えず、そのクエリの結果だけを作り直す
- 版を進める: `uv run scripts/validate.py update-result --release latest queries/<description>`。固定した版の DB でクエリが動かなくなったとき（スキーマの変更に追従したとき）に使う
- 結果が実行のたびに変わらないよう、最終結果の並び順は同じ値の行の順序まで決める。`unique` の列を並び順の末尾に足すと決まる

`checks` は最新の DB で不変条件が成り立つかを見るもので、`result.json` は同じ DB で結果が変わっていないかを見るもの。最初から誤っている結果は `result.json` では検出できない。

## query.sql

- 1 ファイル 1 文で、読み取り専用（SELECT / WITH のみ）(validate)
- 末尾に `;` を付ける (validate)
- 結果が 1 行以上返る (validate)
- テーブル名・カラム名は `TABLE.sqlite3.md` に従う。テーブルや列の使い分け（所属チームの引き方など）は、該当テーブルの注記（`>` で始まる行）を読んで従う
- SQLite と DuckDB の両方で動く書き方にする。どちらか一方にしかない関数や構文は使わない (validate)
- 出力カラムの別名はなるべく日本語にする（例: `AS プレイヤー名`）
- シーズンは `start_year` を使う
- 順序に意味がある処理（連続記録、何番目か、直前との比較）では、並び順に使う列が実際にその順序を表しているか確かめる。区分を表す文字列（ステージ名など）は文字列順に並ぶため、時系列の並び順に入れない
- 件数を絞るときは、同数の場合の順序まで決める。絞り込みの並び順、最終結果の並び順、plan の説明を一致させる

### コメント

- コメントは `-- ` だけを使い、`/* */` は使わない (validate)
- CTE の直前に、その処理の目的を書く (validate)
- 最後の SELECT の前に、出力内容を書く
- まとまりのある JOIN 群・カラム群・CASE 式の先頭に、意図を書く

```sql
-- 各局でのリーチ順序を特定する
WITH reach_with_order AS (
    SELECT
        re.actor_player_id,
        e.kyoku_id,
        ROW_NUMBER() OVER (PARTITION BY e.kyoku_id ORDER BY e.event_order) AS reach_rank
    FROM reach_event re
    JOIN event e ON re.event_id = e.id
    WHERE re.is_accepted = 1
),
-- シーズン・ステージ・プレイヤーごとのリーチ統計を集計する
player_reach_stats AS (
    SELECT
        ls.start_year,
        ss.stage,
        p.name AS player_name,
        t.name AS team_name,
        -- リーチ回数の集計
        COUNT(*) AS reach_count,
        SUM(CASE WHEN rwo.reach_rank = 1 THEN 1 ELSE 0 END) AS sensei_reach_count
    FROM reach_with_order rwo
    -- プレイヤー情報の結合
    JOIN player p ON rwo.actor_player_id = p.id
    -- 局・試合・シーズン情報の結合
    JOIN kyoku k ON rwo.kyoku_id = k.id
    JOIN game g ON k.game_id = g.id
    JOIN season_stage ss ON g.season_stage_id = ss.id
    JOIN league_season ls ON ss.league_season_id = ls.id
    -- 試合時点の所属チームの結合
    JOIN game_player_result gpr ON g.id = gpr.game_id AND p.id = gpr.player_id
    JOIN team t ON gpr.team_id = t.id
    GROUP BY ls.start_year, ss.stage, p.id, t.name
)
-- 最終結果: 先制リーチ率を算出して出力
SELECT
    start_year || '-' || (start_year + 1) AS シーズン,
    stage AS ステージ,
    player_name AS プレイヤー名,
    team_name AS チーム名,
    reach_count AS リーチ回数,
    sensei_reach_count AS 先制リーチ回数,
    ROUND(sensei_reach_count * 100.0 / reach_count, 2) AS 先制リーチ率
FROM player_reach_stats
ORDER BY start_year DESC, stage, 先制リーチ率 DESC;
```
