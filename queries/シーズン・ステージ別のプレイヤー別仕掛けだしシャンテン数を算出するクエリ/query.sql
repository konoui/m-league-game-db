-- 仕掛けだし（その局で最初の仕掛け）と、仕掛ける直前の標準形シャンテン数を集める
-- 仕掛けはチー・ポン・大明槓で、加槓・暗槓は副露率の定義に合わせて含めない
WITH first_furo AS (
    SELECT event_id, actor_player_id, before_shanten_count FROM chi_event WHERE furo_count = 1
    UNION ALL
    SELECT event_id, actor_player_id, before_shanten_count FROM pon_event WHERE furo_count = 1
    UNION ALL
    SELECT event_id, actor_player_id, before_shanten_count FROM daiminkan_event WHERE furo_count = 1
),
-- シーズン・ステージ・プレイヤーごとに仕掛けだしシャンテン数を集計する
player_first_furo_stats AS (
    SELECT
        ls.start_year,
        ss.stage,
        p.name AS player_name,
        t.name AS team_name,
        -- 仕掛けた局数と平均シャンテン数
        COUNT(*) AS furo_kyoku_count,
        AVG(ff.before_shanten_count) AS avg_shanten,
        -- シャンテン数ごとの内訳
        SUM(CASE WHEN ff.before_shanten_count = 0 THEN 1 ELSE 0 END) AS shanten0_count,
        SUM(CASE WHEN ff.before_shanten_count = 1 THEN 1 ELSE 0 END) AS shanten1_count,
        SUM(CASE WHEN ff.before_shanten_count = 2 THEN 1 ELSE 0 END) AS shanten2_count,
        SUM(CASE WHEN ff.before_shanten_count >= 3 THEN 1 ELSE 0 END) AS shanten3_over_count
    FROM first_furo ff
    -- プレイヤー情報の結合
    JOIN player p ON ff.actor_player_id = p.id
    -- イベント・局・試合・シーズン情報の結合
    JOIN event e ON ff.event_id = e.id
    JOIN kyoku k ON e.kyoku_id = k.id
    JOIN game g ON k.game_id = g.id
    JOIN season_stage ss ON g.season_stage_id = ss.id
    JOIN league_season ls ON ss.league_season_id = ls.id
    -- チーム所属情報の結合
    JOIN player_team pt ON p.id = pt.player_id
        AND ls.start_year >= pt.joined_season_year
        AND ls.start_year <= pt.left_season_year
    JOIN team t ON pt.team_id = t.id
    GROUP BY ls.start_year, ss.stage, p.id, p.name, t.name
)
-- 最終結果: 平均仕掛けだしシャンテン数とシャンテン数ごとの割合を出力する
SELECT
    start_year || '-' || (start_year + 1) AS シーズン,
    stage AS ステージ,
    player_name AS プレイヤー名,
    team_name AS チーム名,
    furo_kyoku_count AS 仕掛け局数,
    ROUND(avg_shanten, 2) AS 平均仕掛けだしシャンテン数,
    -- シャンテン数ごとの仕掛けの割合
    ROUND(shanten0_count * 100.0 / furo_kyoku_count, 2) AS 聴牌からの仕掛け率,
    ROUND(shanten1_count * 100.0 / furo_kyoku_count, 2) AS 一シャンテンからの仕掛け率,
    ROUND(shanten2_count * 100.0 / furo_kyoku_count, 2) AS 二シャンテンからの仕掛け率,
    ROUND(shanten3_over_count * 100.0 / furo_kyoku_count, 2) AS 三シャンテン以上からの仕掛け率
FROM player_first_furo_stats
ORDER BY start_year DESC, stage, 平均仕掛けだしシャンテン数 DESC, player_name;
