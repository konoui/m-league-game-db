# よく使う SQL の型

どれも m-league-db の `run_sql` で動作を確認済み。選手名・期間・条件を差し替えて使う。

## 目次

1. 連続記録（連続1着・連続4着・連続連対など）
2. シーズン成績の率ランキング
3. 2 人の直接対決
4. 役満など特定の和了の一覧
5. 生の行での確認

---

## 1. 連続記録

選手ごとに出場試合を時系列に並べ、条件を満たす試合が途切れるまでを 1 つの記録として数える（gaps-and-islands）。シーズンをまたいで数える形。シーズン・ステージで区切りたいときは、2 つの `PARTITION BY gpr.player_id` に `ls.start_year, ss.stage` を足す。

条件は `WHERE rank = 4` の部分を差し替える（連続1着 `rank = 1`、連続連対 `rank <= 2`、連続ラス回避 `rank < 4`）。

```sql
WITH g AS (
  SELECT gpr.player_id, gpr.team_id, gpr.rank, ga.date, ga.day_game_number, ls.start_year, ss.stage,
         ROW_NUMBER() OVER (PARTITION BY gpr.player_id ORDER BY ga.date, ga.day_game_number) AS seq
  FROM game_player_result gpr
  JOIN game ga ON ga.id = gpr.game_id
  JOIN season_stage ss ON ss.id = ga.season_stage_id
  JOIN league_season ls ON ls.id = ss.league_season_id
),
s AS (SELECT *, seq - ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY seq) AS grp FROM g WHERE rank = 4),
streaks AS (
  SELECT player_id, grp, COUNT(*) AS n, MIN(date) AS 開始日, MAX(date) AS 終了日,
         arg_min(start_year || '-' || (start_year + 1) || ' ' || stage, seq) AS 開始時,
         arg_max(start_year || '-' || (start_year + 1) || ' ' || stage, seq) AS 終了時,
         arg_min(team_id, seq) AS team_id
  FROM s GROUP BY player_id, grp
)
SELECT p.name AS 選手, t.name AS チーム, n AS 連続回数, 開始日, 終了日, 開始時, 終了時
FROM streaks st JOIN player p ON p.id = st.player_id JOIN team t ON t.id = st.team_id
ORDER BY n DESC, 開始日
LIMIT 10
```

`開始時` と `終了時` が違う行は、シーズンやステージをまたいだ記録。区切った数え方では別の記録に分かれる。

チーム単位の連続記録は、`player_id` を `team_id` に置き換え、1 試合に同じチームの選手が 1 人しか出ないことを前提に同じ形で書ける。

## 2. シーズン成績の率ランキング

定型の率は集計済みビューにある。試合数の下限を必ず置く。

```sql
SELECT player_name AS 選手, team_name AS チーム, total_game_count AS 試合数,
       rank1_count AS トップ回数, ROUND(top_per_game_percent, 1) AS "トップ率(%)",
       ROUND(top2_per_game_percent, 1) AS "連対率(%)", CAST(league_points_total AS DECIMAL(8,1)) AS ポイント
FROM player_season_stage_stats
WHERE season_start_year = 2025 AND stage = 'regular' AND total_game_count >= 20
ORDER BY top_per_game_percent DESC
LIMIT 5
```

ビューの主な列: `top_per_game_percent`（トップ率）、`top2_per_game_percent`（連対率）、`avoid_last_per_game_percent`（ラス回避率）、`agari_per_kyoku_percent`（和了率）、`dealin_per_kyoku_percent`（放銃率）、`reach_per_kyoku_percent`（リーチ率）、`furo_per_kyoku_percent`（副露率）、`agari_points_per_agari`（平均打点）、`league_points_total`（ポイント）。全列は `describe_table("player_season_stage_stats")`。

通算の率は、ビューの回数の列（`rank1_count` など）と `total_game_count` を選手ごとに SUM してから割る。率の列を平均しない（試合数で重みが変わるため）。

## 3. 2 人の直接対決

同じ試合に出た回数と、どちらが上の着順だったか。

```sql
WITH a AS (SELECT gpr.game_id, gpr.rank, gpr.league_points FROM game_player_result gpr JOIN player p ON p.id = gpr.player_id WHERE p.name = '佐々木寿人'),
     b AS (SELECT gpr.game_id, gpr.rank, gpr.league_points FROM game_player_result gpr JOIN player p ON p.id = gpr.player_id WHERE p.name = '多井隆晴')
SELECT COUNT(*) AS 同卓数,
       SUM(CASE WHEN a.rank < b.rank THEN 1 ELSE 0 END) AS 佐々木が上,
       SUM(CASE WHEN a.rank > b.rank THEN 1 ELSE 0 END) AS 多井が上,
       CAST(SUM(a.league_points) AS DECIMAL(8,1)) AS 佐々木pt,
       CAST(SUM(b.league_points) AS DECIMAL(8,1)) AS 多井pt
FROM a JOIN b USING (game_id)
```

選手名は先に `find_player` で正式表記を確かめる。

## 4. 役満など特定の和了の一覧

和了（`agari_event`）は `event` → `kyoku` → `game` とたどって試合日を得る。役は `agari_yaku` と `yaku_name`。役満の役は翻数 13 以上で記録されている。

```sql
SELECT ga.date AS 試合日, p.name AS 和了者, e.type AS 和了方法,
       string_agg(yn.name, '・' ORDER BY yn.id) FILTER (WHERE ay.han >= 13) AS 役満,
       ae.agari_points AS 打点
FROM agari_event ae
JOIN event e ON e.id = ae.event_id
JOIN kyoku k ON k.id = e.kyoku_id
JOIN game ga ON ga.id = k.game_id
JOIN player p ON p.id = ae.actor_player_id
JOIN agari_yaku ay ON ay.agari_event_id = ae.event_id
JOIN yaku_name yn ON yn.id = ay.yaku_name_id
WHERE ae.is_yakuman = 1
GROUP BY ALL
ORDER BY ga.date DESC
```

`e.type` は 'tsumo' / 'ron'。ロンの放銃者は `ae.target_player_id`。三倍満は `is_yakuman = 0 AND han >= 11`、倍満は `han BETWEEN 8 AND 10`。

## 5. 生の行での確認

集計の 1 位について、該当期間の試合を並べて数え直す。

```sql
SELECT ga.date AS 試合日, ga.day_game_number AS 第何試合, gpr.rank AS 着順, gpr.score AS 素点,
       CAST(gpr.league_points AS DECIMAL(6,1)) AS ポイント
FROM game_player_result gpr
JOIN game ga ON ga.id = gpr.game_id
JOIN player p ON p.id = gpr.player_id
WHERE p.name = '岡田紗佳' AND ga.date BETWEEN '2024-10-01' AND '2024-12-31'
ORDER BY ga.date, ga.day_game_number
```

期間は記録の前後に 1 試合ずつ余裕を持たせ、記録の直前・直後で条件が途切れていることも見る。
