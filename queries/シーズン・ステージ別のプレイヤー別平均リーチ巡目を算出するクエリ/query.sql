-- 受け入れられたリーチごとに、リーチ宣言牌を打った時点の巡目を取得する
-- リーチイベントの直後のイベントがリーチ者の宣言牌の打牌になる
WITH reach_turn AS (
    SELECT
        re.actor_player_id,
        e.kyoku_id,
        ps.turn_number
    FROM reach_event re
    JOIN event e ON re.event_id = e.id
    -- リーチ宣言牌の打牌イベントとその時点のリーチ者の状態の結合
    JOIN event de ON de.kyoku_id = e.kyoku_id
        AND de.event_order = e.event_order + 1
    JOIN player_state ps ON ps.event_id = de.id
        AND ps.player_id = re.actor_player_id
    WHERE re.is_accepted = 1
),
-- シーズン・ステージ・プレイヤーごとにリーチ巡目を集計する
player_reach_turn_stats AS (
    SELECT
        ls.start_year,
        ss.stage,
        p.name AS player_name,
        t.name AS team_name,
        -- リーチ回数と平均リーチ巡目
        COUNT(*) AS reach_count,
        AVG(rt.turn_number) AS avg_reach_turn,
        -- 序盤・中盤・終盤ごとのリーチ回数
        SUM(CASE WHEN rt.turn_number <= 6 THEN 1 ELSE 0 END) AS early_reach_count,
        SUM(CASE WHEN rt.turn_number BETWEEN 7 AND 12 THEN 1 ELSE 0 END) AS middle_reach_count,
        SUM(CASE WHEN rt.turn_number >= 13 THEN 1 ELSE 0 END) AS late_reach_count
    FROM reach_turn rt
    -- プレイヤー情報の結合
    JOIN player p ON rt.actor_player_id = p.id
    -- 局・試合・シーズン情報の結合
    JOIN kyoku k ON rt.kyoku_id = k.id
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
-- 最終結果: 平均リーチ巡目と序盤・中盤・終盤ごとのリーチの割合を出力する
SELECT
    start_year || '-' || (start_year + 1) AS シーズン,
    stage AS ステージ,
    player_name AS プレイヤー名,
    team_name AS チーム名,
    reach_count AS リーチ回数,
    ROUND(avg_reach_turn, 2) AS 平均リーチ巡目,
    -- 序盤・中盤・終盤ごとのリーチの割合
    ROUND(early_reach_count * 100.0 / reach_count, 2) AS 序盤リーチ率,
    ROUND(middle_reach_count * 100.0 / reach_count, 2) AS 中盤リーチ率,
    ROUND(late_reach_count * 100.0 / reach_count, 2) AS 終盤リーチ率
FROM player_reach_turn_stats
ORDER BY start_year DESC, stage, 平均リーチ巡目, player_name;
