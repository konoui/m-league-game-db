# DB 変更履歴

データベースのスキーマ変更の記録。新しいものを上に足していく。
古い SQL を書き換えるときは、使っているリリースより新しい項目を順に見る。

命名の考え方そのものは DB_NAMING.md を参照。

<!--
新しい項目の書き方:

## <リリースタグ、未リリースなら「未リリース」>

互換性のない変更があれば、その旨を最初に 1 行で書く。
変更の種類ごとに「テーブル名」「列名」「廃止した列」「追加した列」の見出しを立て、
旧名・新名・備考の表で書く。値や意味が変わる場合は「移行のしかた」に書く。
-->

## 未リリース

命名を全面的に見直した。**このリリースより前に書いた SQL は書き換えが必要**。
対応表は、リリース済みのスキーマと新しいスキーマを機械的に突き合わせて作り、
旧名が旧スキーマに、新名が新スキーマに実在することを検証している。

### テーブル名

イベントそのものではなく、イベントに付随するデータなので接尾辞の `_event` を外した。

| 旧                      | 新                |
| ----------------------- | ----------------- |
| `agari_yaku_event`      | `agari_yaku`      |
| `ryukyoku_player_event` | `ryukyoku_player` |
| `tenpai_yaku_event`     | `tenpai_yaku`     |

### 列名

#### agari_event

| 旧             | 新                   | 備考                   |
| -------------- | -------------------- | ---------------------- |
| `winning_tile` | `agari_tile`         |                        |
| `winning_type` | `agari_waiting_type` | 和了牌が入った面子の形 |
| `base_points`  | `agari_points`       | 和了点                 |

#### agari_yaku（旧 agari_yaku_event）

| 旧        | 新             | 備考 |
| --------- | -------------- | ---- |
| `name_id` | `yaku_name_id` |      |

#### tenpai_yaku（旧 tenpai_yaku_event）

| 旧        | 新             | 備考 |
| --------- | -------------- | ---- |
| `name_id` | `yaku_name_id` |      |

#### ryukyoku_player（旧 ryukyoku_player_event）

| 旧       | 新              | 備考       |
| -------- | --------------- | ---------- |
| `points` | `tenpai_points` | テンパイ料 |

#### dora_indicator_event

| 旧               | 新                    | 備考 |
| ---------------- | --------------------- | ---- |
| `type`           | `dora_type`           |      |
| `dora_indicator` | `dora_indicator_tile` |      |
| `dora`           | `dora_tile`           |      |

#### draw_event

| 旧               | 新                     | 備考 |
| ---------------- | ---------------------- | ---- |
| `wall_remaining` | `wall_remaining_count` |      |

#### foul_play

| 旧               | 新                      | 備考 |
| ---------------- | ----------------------- | ---- |
| `type`           | `foul_type`             |      |
| `penalty_points` | `penalty_league_points` | pt   |

#### game

| 旧             | 新                  | 備考                 |
| -------------- | ------------------- | -------------------- |
| `match_number` | `day_game_number`   | その日の何試合目か   |
| `round_number` | `stage_game_number` | ステージ内の通し番号 |

#### game_player_result

| 旧               | 新                      | 備考 |
| ---------------- | ----------------------- | ---- |
| `points`         | `league_points`         | pt   |
| `penalty_points` | `penalty_league_points` | pt   |

#### haipai_event

| 旧               | 新                  | 備考 |
| ---------------- | ------------------- | ---- |
| `player_id`      | `actor_player_id`   |      |
| `tenho_possible` | `is_tenho_possible` |      |
| `chiho_possible` | `is_chiho_possible` |      |

#### kyoku

| 旧                  | 新              | 備考                   |
| ------------------- | --------------- | ---------------------- |
| `parent_player_id`  | `oya_player_id` |                        |
| `reach_stick_count` | `kyotaku_count` | 局の開始時の供託の本数 |

#### player_tenpai_state

| 旧                           | 新                          | 備考 |
| ---------------------------- | --------------------------- | ---- |
| `tile_types_count`           | `tile_type_count`           |      |
| `ideal_tiles_count`          | `ideal_tile_count`          |      |
| `available_tiles_count`      | `available_tile_count`      |      |
| `discarded_tiles_count`      | `discarded_tile_count`      |      |
| `dora_indicator_tiles_count` | `dora_indicator_tile_count` |      |

#### tenpai_agari_matrix

| 旧                | 新         | 備考 |
| ----------------- | ---------- | ---- |
| `tenpai_event_id` | `event_id` |      |

#### team_season_stage_result

| 旧                         | 新                    | 備考                |
| -------------------------- | --------------------- | ------------------- |
| `base_points`              | `stage_league_points` | そのステージ分の pt |
| `final_points`             | `final_league_points` | 持ち越しを加えた pt |
| `league_season_start_year` | `season_start_year`   |                     |
| `league_season_end_year`   | `season_end_year`     |                     |

#### player_season_stage_stats_base

| 旧                               | 新                                               | 備考       |
| -------------------------------- | ------------------------------------------------ | ---------- |
| `start_season_year`              | `season_start_year`                              |            |
| `win_count`                      | `agari_count`                                    |            |
| `win_point_total`                | `agari_points_total`                             |            |
| `tsumo_win_count`                | `tsumo_agari_count`                              |            |
| `ura_dora_win_count`             | `ura_dora_agari_count`                           |            |
| `dealin_point_total`             | `dealin_points_total`                            |            |
| `tenpai_point_total`             | `tenpai_points_total`                            |            |
| `itai_oya_kaburi_point_total`    | `itai_oya_kaburi_points_total`                   |            |
| `carryover_kyotaku_point_total`  | `carryover_kyotaku_points_total`                 |            |
| `tsuminashi_kyotaku_point_total` | `kyotaku_points_excluding_own_reach_total`       | 意味は同じ |
| `kyotaku_point_total`            | `kyotaku_honba_points_excluding_own_reach_total` | 意味は同じ |
| `total_points`                   | `league_points_total`                            | pt         |

#### player_season_stage_stats

| 旧                                | 新                                               | 備考       |
| --------------------------------- | ------------------------------------------------ | ---------- |
| `start_season_year`               | `season_start_year`                              |            |
| `win_rate_percent`                | `agari_per_kyoku_percent`                        |            |
| `tsumo_win_rate_percent`          | `tsumo_agari_per_agari_percent`                  |            |
| `reach_agari_in_win_rate_percent` | `reach_agari_per_agari_percent`                  |            |
| `furo_agari_in_win_rate_percent`  | `furo_agari_per_agari_percent`                   |            |
| `dama_agari_in_win_rate_percent`  | `dama_agari_per_agari_percent`                   |            |
| `dealin_rate_percent`             | `dealin_per_kyoku_percent`                       |            |
| `hitsumo_rate_percent`            | `hitsumo_per_kyoku_percent`                      |            |
| `furo_rate_percent`               | `furo_per_kyoku_percent`                         |            |
| `reach_rate_percent`              | `reach_per_kyoku_percent`                        |            |
| `reach_agari_rate_percent`        | `reach_agari_per_reach_percent`                  |            |
| `reach_dealin_rate_percent`       | `reach_dealin_per_reach_percent`                 |            |
| `ryukyoku_rate_percent`           | `ryukyoku_per_kyoku_percent`                     |            |
| `tenpai_rate_percent`             | `tenpai_per_ryukyoku_percent`                    |            |
| `tenpai_point_balance`            | `tenpai_points_per_ryukyoku`                     |            |
| `oya_kaburi_rate_percent`         | `oya_kaburi_per_oya_kyoku_percent`               |            |
| `itai_oya_kaburi_rate_percent`    | `itai_oya_kaburi_per_oya_kaburi_percent`         |            |
| `renchan_rate_percent`            | `renchan_per_oya_kyoku_percent`                  |            |
| `ura_dora_nori_rate_percent`      | `ura_dora_agari_per_reach_agari_percent`         |            |
| `top_rate_percent`                | `top_per_game_percent`                           |            |
| `top2_rate_percent`               | `top2_per_game_percent`                          |            |
| `avoid_last_rate_percent`         | `avoid_last_per_game_percent`                    |            |
| `yokomove_rate_percent`           | `yokomove_per_kyoku_percent`                     |            |
| `avg_win_points`                  | `agari_points_per_agari`                         |            |
| `avg_dealin_points`               | `dealin_points_per_dealin`                       |            |
| `avg_dora_num`                    | `dora_per_agari`                                 |            |
| `avg_aka_dora_num`                | `aka_dora_per_agari`                             |            |
| `avg_all_dora_num`                | `all_dora_per_agari`                             |            |
| `avg_ura_dora_num`                | `ura_dora_per_reach_agari`                       |            |
| `carryover_kyotaku_point_total`   | `carryover_kyotaku_points_total`                 |            |
| `tsuminashi_kyotaku_point_total`  | `kyotaku_points_excluding_own_reach_total`       | 意味は同じ |
| `kyotaku_point_total`             | `kyotaku_honba_points_excluding_own_reach_total` | 意味は同じ |
| `total_points`                    | `league_points_total`                            | pt         |

### 廃止した列

| テーブル      | 旧列     | 置き換え                                                                                |
| ------------- | -------- | --------------------------------------------------------------------------------------- |
| `agari_event` | `points` | `revenue_points`（生成列）が同じ値。内訳は agari_points / honba_points / kyotaku_points |

### 追加した列

既存の SQL を壊すものではないが、使えるようになった列。

| テーブル / ビュー                | 列                     |
| -------------------------------- | ---------------------- |
| `agari_event`                    | `honba_points`         |
| `agari_event`                    | `kyotaku_points`       |
| `agari_event`                    | `revenue_points`       |
| `ankan_event`                    | `after_shanten_count`  |
| `ankan_event`                    | `before_shanten_count` |
| `ankan_event`                    | `tile`                 |
| `game_player_result`             | `team_id`              |
| `player_season_stage_stats`      | `honba_points_total`   |
| `player_season_stage_stats_base` | `honba_points_total`   |
| `shominkan_event`                | `after_shanten_count`  |
| `shominkan_event`                | `before_shanten_count` |
| `tenpai_agari_matrix`            | `player_id`            |
| `yaku_name`                      | `is_yakuman`           |

### 移行のしかた

- 列名・テーブル名が変わるため、既存のデータベースに追記する形では移行できない。データベースを作り直す。
- 値そのものは変わっていない。改名前後で全ビューの値が一致することを確認済み。
  例外は 1 件で、`kyotaku_points_excluding_own_reach_total` が積み棒の特例局を含む選手で 300 変わる（本場の加点を実際の値で計算するようにしたため）。
- `agari_event.revenue_points` は生成列のため、`SELECT` では普通の列として使えるが `PRAGMA table_info` には現れない（`PRAGMA table_xinfo` には出る）。
