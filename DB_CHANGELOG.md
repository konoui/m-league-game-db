# DB 変更履歴

データベースのスキーマ変更の記録。新しいものを上に足していく。

命名の考え方そのものは DB_NAMING.md を参照。

<!--
新しい項目の書き方:

## <変更の内容>

互換性のない変更があれば、その旨を最初に 1 行で書く。
変更の種類ごとに「テーブル名」「列名」「廃止した列」「追加した列」の見出しを立て、
旧名・新名・備考の表で書く。値や意味が変わる場合は「移行のしかた」に書く。
-->

## 2018-19 シーズンのファイナルの持ち越しを直した

`team_season_stage_result.final_league_points` の 2018-19 の final の行の値が変わる。
セミファイナルがないシーズンでも、セミファイナルがある場合と同じ式で計算していたため、レギュラーの 1/4 しか持ち越していなかった。
今はレギュラーの半分を持ち越す。2019-20 以降の値は変わらない。

## 見逃しのフリテンと、他家の打牌時点の聴牌者の状態を記録するようにした

**player_tenpai_state・tenpai_agari_matrix の行の意味が変わり、`player_state.is_furiten`・`player_state.is_reached` は player_tenpai_state に移した**。
これまでは 1 イベントに打牌者の 1 行だけだったが、他家の打牌・加槓の時点で聴牌している人の行も入る。
player_state は今までどおり本人の配牌・打牌と流局時の行だけで、他家の行は入らない。

### player_tenpai_state に追加した列

| 列                     | 内容                                                                               |
| ---------------------- | ---------------------------------------------------------------------------------- |
| `is_actor`             | そのイベントの主体（配牌・打牌した人）の行か。他家の聴牌者の行と流局時の行は false |
| `is_reached`           | リーチ状態か。player_state から移した                                              |
| `is_furiten`           | フリテン状態か（下の 3 つの理由のいずれか）。player_state から移した              |
| `is_discard_furiten`   | 自分の捨て牌に待ち牌がある（捨て牌フリテン）                                       |
| `is_temporary_furiten` | リーチ前に、役があってロンできる牌を見逃した（同巡内フリテン）                     |
| `is_reach_furiten`     | リーチ後に、役があってロンできる牌を見逃した（局の終わりまで続く）                 |

### tenpai_agari_matrix に追加した列

待ち牌ごとの枚数。ロンとツモの行に同じ値が入るので、合計するときは、重複を避けるため `DISTINCT` を使う。

| 列                          | 内容                                                       |
| --------------------------- | ---------------------------------------------------------- |
| `ideal_tile_count`          | その待ち牌の理論上の枚数（4 から自分の手牌にある枚数を引く） |
| `discarded_tile_count`      | その待ち牌が捨て牌（全員の河）にある枚数                    |
| `dora_indicator_tile_count` | その待ち牌がドラ表示牌として見えている枚数                  |

### 追加したビュー

| ビュー                       | 内容                                                                                                |
| ---------------------------- | --------------------------------------------------------------------------------------------------- |
| `player_tenpai_waiting_tile` | `tenpai_agari_matrix` を待ち牌ごとの 1 行にしたもの。待ち牌すべての合計（`total_` の列）も引ける |

### 廃止した列

| 列                        | 移行先                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------ |
| `player_state.is_furiten` | `player_tenpai_state.is_furiten`（聴牌していなければ行がないのでフリテンでもない）         |
| `player_state.is_reached` | `player_tenpai_state.is_reached`（リーチは聴牌が条件なので、行がなければリーチしていない） |

### 値が変わる列

| 列                                   | 変更前                   | 変更後                                                    |
| ------------------------------------ | ------------------------ | --------------------------------------------------------- |
| `is_furiten`                         | 捨て牌フリテンのみ       | 上の 3 つの理由のいずれか                                 |
| `tenpai_agari_matrix` のロンの行     | フリテン中でも作っていた | フリテン中は作らない（行の有無 = その時点で和了できるか） |
| `tenpai_yaku`（他家の行のロンの行）  | （他家の行はなかった）   | 最後の打牌では河底撈魚、加槓では加えた牌に搶槓を含む      |
| `tenpai_agari_matrix` の流局イベント | 作っていなかった         | 「流局しなければ和了できた牌」として作る                  |

### 移行のしかた

- `player_state.is_furiten`・`player_state.is_reached` を使っていた SQL は、同じ `(event_id, player_id)` の `player_tenpai_state` の同名の列を使う。行がなければどちらも false として扱う。
- player_tenpai_state・tenpai_agari_matrix で本人の状態だけを集計する SQL は `player_tenpai_state.is_actor = 1` を足す。matrix をイベントだけで結合すると、同じイベントの他家の聴牌者の行も含まれる。
- 役の有無だけを見たい（フリテンを無視したい）場合は、フリテンになる前の行を参照する。

命名を全面的に見直した。**この変更より前に書いた SQL は書き換えが必要**。
対応表は、変更前のスキーマと変更後のスキーマを機械的に突き合わせて作り、
旧名が旧スキーマに、新名が新スキーマに実在することを検証している。

## 牌の並べ方をそろえた

牌を複数持つ列は、すべて `,` 区切りにそろえた。

| 列                                       | 変更前                         | 変更後         |
| ---------------------------------------- | ------------------------------ | -------------- |
| `player_state.hand`, `haipai_event.hand` | 配牌時だけ `279m1569p1168s35z` | `2m,7m,9m,...` |
| `player_tenpai_state.waiting_tiles`      | 区切りなし（`1m4m7m`）         | `1m,4m,7m`     |
| `player_state_called_block.tiles`        | 区切りなし（`1z1z1z`）         | `1z,1z,1z`     |

牌の中身は変わっていない（区切り文字が入るだけ）。これらの列を文字列として解析していた場合は書き換えが必要。

## DuckDB 版だけの違い

牌を複数持つ列は、DuckDB 版では配列 (`VARCHAR[]`) になっている。`list_contains` や `unnest` が使える。

| 列                                                                                                               |
| ---------------------------------------------------------------------------------------------------------------- |
| `player_state.hand`, `haipai_event.hand`, `player_tenpai_state.waiting_tiles`, `player_state_called_block.tiles` |

SQLite 版は `,` 区切りの文字列のまま。`str_split` で同じ形にできる。

また DuckDB 版は、主キーと外部キーを制約として定義していない（索引が張られ、ファイルが数倍に膨らむため）。
テーブル定義に書かれている主キー・外部キーは、行の粒度と結合の手がかりとして読む。

## 追加したテーブル

| テーブル                    | 内容                                                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| `player_state_called_block` | `player_state.called_blocks` を 1 面子 1 行に分解したもの。文字列を解析せずに鳴きの種類や出所を引ける |

`called_blocks` はそのまま残しているので、既存の SQL は書き換えなくてよい。

## テーブル名

イベントそのものではなく、イベントに付随するデータなので接尾辞の `_event` を外した。

| 旧                      | 新                |
| ----------------------- | ----------------- |
| `agari_yaku_event`      | `agari_yaku`      |
| `ryukyoku_player_event` | `ryukyoku_player` |
| `tenpai_yaku_event`     | `tenpai_yaku`     |

## 列名

### agari_event

| 旧             | 新                   | 備考                   |
| -------------- | -------------------- | ---------------------- |
| `winning_tile` | `agari_tile`         |                        |
| `winning_type` | `agari_waiting_type` | 和了牌が入った面子の形 |
| `base_points`  | `agari_points`       | 和了点                 |

### agari_yaku（旧 agari_yaku_event）

| 旧        | 新             | 備考 |
| --------- | -------------- | ---- |
| `name_id` | `yaku_name_id` |      |

### tenpai_yaku（旧 tenpai_yaku_event）

| 旧        | 新             | 備考 |
| --------- | -------------- | ---- |
| `name_id` | `yaku_name_id` |      |

### ryukyoku_player（旧 ryukyoku_player_event）

| 旧       | 新              | 備考       |
| -------- | --------------- | ---------- |
| `points` | `tenpai_points` | テンパイ料 |

### dora_indicator_event

| 旧               | 新                    | 備考 |
| ---------------- | --------------------- | ---- |
| `type`           | `dora_type`           |      |
| `dora_indicator` | `dora_indicator_tile` |      |
| `dora`           | `dora_tile`           |      |

### draw_event

| 旧               | 新                     | 備考 |
| ---------------- | ---------------------- | ---- |
| `wall_remaining` | `wall_remaining_count` |      |

### foul_play

| 旧               | 新                      | 備考 |
| ---------------- | ----------------------- | ---- |
| `type`           | `foul_type`             |      |
| `penalty_points` | `penalty_league_points` | pt   |

### game

| 旧             | 新                  | 備考                 |
| -------------- | ------------------- | -------------------- |
| `match_number` | `day_game_number`   | その日の何試合目か   |
| `round_number` | `stage_game_number` | ステージ内の通し番号 |

### game_player_result

| 旧               | 新                      | 備考 |
| ---------------- | ----------------------- | ---- |
| `points`         | `league_points`         | pt   |
| `penalty_points` | `penalty_league_points` | pt   |

### haipai_event

| 旧               | 新                  | 備考 |
| ---------------- | ------------------- | ---- |
| `player_id`      | `actor_player_id`   |      |
| `tenho_possible` | `is_tenho_possible` |      |
| `chiho_possible` | `is_chiho_possible` |      |

### kyoku

| 旧                  | 新              | 備考                   |
| ------------------- | --------------- | ---------------------- |
| `parent_player_id`  | `oya_player_id` |                        |
| `reach_stick_count` | `kyotaku_count` | 局の開始時の供託の本数 |

### player_tenpai_state

| 旧                           | 新                          | 備考 |
| ---------------------------- | --------------------------- | ---- |
| `tile_types_count`           | `tile_type_count`           |      |
| `ideal_tiles_count`          | `ideal_tile_count`          |      |
| `available_tiles_count`      | `available_tile_count`      |      |
| `discarded_tiles_count`      | `discarded_tile_count`      |      |
| `dora_indicator_tiles_count` | `dora_indicator_tile_count` |      |

### tenpai_agari_matrix

| 旧                | 新         | 備考 |
| ----------------- | ---------- | ---- |
| `tenpai_event_id` | `event_id` |      |

### team_season_stage_result

| 旧                         | 新                    | 備考                |
| -------------------------- | --------------------- | ------------------- |
| `base_points`              | `stage_league_points` | そのステージ分の pt |
| `final_points`             | `final_league_points` | 持ち越しを加えた pt |
| `league_season_start_year` | `season_start_year`   |                     |
| `league_season_end_year`   | `season_end_year`     |                     |

### player_season_stage_stats_base

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

### player_season_stage_stats

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

## 廃止した列

| テーブル      | 旧列     | 置き換え                                                                                |
| ------------- | -------- | --------------------------------------------------------------------------------------- |
| `agari_event` | `points` | `revenue_points`（生成列）が同じ値。内訳は agari_points / honba_points / kyotaku_points |

## 追加した列

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

## 移行のしかた

- 列名・テーブル名が変わるため、既存のデータベースに追記する形では移行できない。データベースを作り直す。
- 値そのものは変わっていない。改名前後で全ビューの値が一致することを確認済み。
  例外は 1 件で、`kyotaku_points_excluding_own_reach_total` が積み棒の特例局を含む選手で 300 変わる（本場の加点を実際の値で計算するようにしたため）。
- `agari_event.revenue_points` は生成列のため、`SELECT` では普通の列として使えるが `PRAGMA table_info` には現れない（`PRAGMA table_xinfo` には出る）。
