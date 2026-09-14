# クエリの形式と品質基準

`scripts/validate.py` が機械的に検査するルールには「(validate)」を付けています。付いていないルールは検査されないため、作成者やレビュー担当が確認してください。

## ディレクトリ構成

```
queries/<description>/
  query.sql   # SQL 本体
  meta.json   # description, plan, tables（schema/meta.schema.json）
```

- ディレクトリ名は `description` と完全に一致させる (validate)
- 置けるファイルは `query.sql` と `meta.json` の 2 つだけ (validate)
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
  "tables": ["reach_event", "event", "player", "kyoku", "game", "season_stage", "league_season", "player_team", "team"]
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

SQL が参照するテーブル・ビューを列挙する。`uv run scripts/validate.py --fix <dir>` を実行すると、実際に参照しているテーブルに合わせて自動で書き換わる (validate)

## query.sql

- 1 ファイル 1 文で、読み取り専用（SELECT / WITH のみ）(validate)
- 末尾に `;` を付ける (validate)
- 結果が 1 行以上返る (validate)
- テーブル名・カラム名は `TABLE.md` に従う
- 出力カラムの別名はなるべく日本語にする（例: `AS プレイヤー名`）
- シーズンは `start_year` を使う。所属チームは `player_team` の `joined_season_year` 〜 `left_season_year` の範囲で絞り込む

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
    -- チーム所属情報の結合
    JOIN player_team pt ON p.id = pt.player_id
        AND ls.start_year >= pt.joined_season_year
        AND ls.start_year <= pt.left_season_year
    JOIN team t ON pt.team_id = t.id
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
