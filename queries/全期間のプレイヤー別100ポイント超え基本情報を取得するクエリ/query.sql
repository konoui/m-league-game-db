-- 100ポイント超えの試合結果を取得
     SELECT DISTINCT
       -- 基本情報の出力
       ls.start_year,
       g.date,
       t.name AS team_name,
       p.name AS player_name,
       gpr.league_points
     FROM game_player_result gpr
     -- 試合・シーズン情報の結合
     JOIN game g ON gpr.game_id = g.id
     JOIN season_stage ss ON g.season_stage_id = ss.id
     JOIN league_season ls ON ss.league_season_id = ls.id
     -- プレイヤー・チーム情報の結合
     JOIN player p ON gpr.player_id = p.id
     JOIN player_team pt ON p.id = pt.player_id 
         AND ls.start_year >= pt.joined_season_year 
         AND ls.start_year <= pt.left_season_year
     JOIN team t ON pt.team_id = t.id
     WHERE gpr.league_points > 100
     ORDER BY gpr.league_points DESC, ls.start_year, g.date, p.name;
