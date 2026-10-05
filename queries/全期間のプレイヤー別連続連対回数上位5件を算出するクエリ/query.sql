-- 各プレイヤーの全試合を、シーズンやステージで区切らずに日付順に並べる
WITH player_games AS (
    SELECT
        gpr.player_id,
        g.date,
        g.day_game_number,
        ls.start_year AS season_year,
        t.name AS team_name,
        gpr.rank,
        -- プレイヤーごとの通算の出場順（ステージ名ではなく試合の日付と当日の試合番号で決める）
        ROW_NUMBER() OVER (PARTITION BY gpr.player_id ORDER BY g.date, g.day_game_number, g.id) AS game_sequence
    FROM game_player_result gpr
    -- 試合・シーズン情報の結合
    JOIN game g ON gpr.game_id = g.id
    JOIN season_stage ss ON g.season_stage_id = ss.id
    JOIN league_season ls ON ss.league_season_id = ls.id
    -- 試合時点の所属チームの結合
    JOIN team t ON gpr.team_id = t.id
),
-- 連対（1着または2着）の試合だけを取り出し、出場順が途切れずに続く試合を同じグループにまとめる
streak_groups AS (
    SELECT
        player_id,
        date,
        game_sequence,
        -- 連続グループ識別子（出場順が連続している行は同じ値になる）
        game_sequence - ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY game_sequence) AS streak_group
    FROM player_games
    WHERE rank <= 2
),
-- 連続記録ごとに長さと最初・最後の出場順を求め、長い順（同数なら開始日の早い順）に上位5件へ絞る
top_streaks AS (
    SELECT
        player_id,
        COUNT(*) AS streak_length,
        MIN(game_sequence) AS start_sequence,
        MAX(game_sequence) AS end_sequence,
        MIN(date) AS start_date
    FROM streak_groups
    GROUP BY player_id, streak_group
    ORDER BY streak_length DESC, start_date, player_id
    LIMIT 5
)
-- 最終結果: 連続連対回数の上位5件を、記録の最初と最後の試合の情報とともに出力
SELECT
    p.name AS プレイヤー名,
    sg.team_name AS 記録開始時チーム名,
    ts.streak_length AS 連続連対回数,
    sg.season_year || '-' || (sg.season_year + 1) AS 記録開始シーズン,
    eg.season_year || '-' || (eg.season_year + 1) AS 記録終了シーズン,
    sg.date AS 記録開始日,
    eg.date AS 記録終了日,
    -- 検算用: 記録の最初の試合から最後の試合までの出場試合数を、日付から数え直す
    (
        SELECT COUNT(*)
        FROM player_games pg
        WHERE pg.player_id = ts.player_id
            AND (pg.date > sg.date OR (pg.date = sg.date AND pg.day_game_number >= sg.day_game_number))
            AND (pg.date < eg.date OR (pg.date = eg.date AND pg.day_game_number <= eg.day_game_number))
    ) AS 期間内出場試合数
FROM top_streaks ts
-- プレイヤー情報の結合
JOIN player p ON ts.player_id = p.id
-- 記録の最初の試合と最後の試合の結合
JOIN player_games sg ON ts.player_id = sg.player_id AND ts.start_sequence = sg.game_sequence
JOIN player_games eg ON ts.player_id = eg.player_id AND ts.end_sequence = eg.game_sequence
ORDER BY 連続連対回数 DESC, 記録開始日, プレイヤー名;
