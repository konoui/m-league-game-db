# DB 命名規約

M リーグ（日本の麻雀プロリーグ）の対局記録データベースの命名規約。
テーブル・ビュー・列を追加または変更するときはこの規約に従う。

このデータベースは、人や LLM が SQL を書いて分析に使う。
名前だけを見て意味や単位を取り違えないことを最優先にする。

## 基本

- すべて snake_case にする。
- テーブル名は単数形にする（`player`、`game`、`kyoku`）。
- 1 つの概念には 1 つの語だけを使う。語は[用語集](#用語集)に従う。

## テーブル

| 種類                     | 形                     | 例                                                    |
| ------------------------ | ---------------------- | ----------------------------------------------------- |
| エンティティ             | `<名詞>`               | `player`、`team`、`game`、`kyoku`                     |
| 関連                     | `<名詞>_<名詞>`        | `player_team`                                         |
| イベントの子テーブル     | `<event.type>_event`   | `draw_event`、`discard_event`、`dora_indicator_event` |
| イベントに付随するデータ | `_event` を付けない    | `agari_yaku`、`ryukyoku_player`                       |
| 結果                     | `<単位>_player_result` | `game_player_result`、`kyoku_player_result`           |
| 状態                     | `player_<内容>_state`  | `player_state`、`player_tenpai_state`                 |

対局の進行は `event` テーブルに 1 行ずつ記録し、種別ごとの詳細を子テーブルに持つ。
`_event` は、`event` の 1 行に 1 対 1 で対応する子テーブルだけに付ける。
例外として、`event.type` の `ron` と `tsumo` はどちらも `agari_event` に対応する。

## 主キー

- エンティティは `id`（`integer` の自動採番）にする。
- イベントの子テーブルは `event_id` を主キーにする。
- 関連や付随データは、自然キーの複合主キーにする（例: `(game_id, player_id)`、`(agari_event_id, yaku_name_id)`）。

## 列

| #   | 規則                                                                                                                                                           | 例                                                            |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| R1  | 持ち点（残高）は `score`、点棒単位の点数は内容を表す接頭辞を付けた `<内容>_points`、M リーグの pt は `*league_points` にする。接頭辞のない `points` は使わない | `score`、`agari_points`、`honba_points`、`league_points`      |
| R2  | 外部キー列は「参照先テーブル名 + `_id`」にする。役割を区別するときだけ `<役割>_player_id` にする                                                               | `kyoku_id`、`yaku_name_id`、`oya_player_id`                   |
| R3  | イベントの主体は `actor_player_id`、状態や結果の対象は `player_id`、牌を出した相手は `target_player_id` にする                                                 | `draw_event.actor_player_id`、`player_state.player_id`        |
| R4  | boolean 列は `is_` で始める                                                                                                                                    | `is_tsumogiri`、`is_tenho_possible`                           |
| R5  | 件数は `<単数名詞>_count` にする                                                                                                                               | `honba_count`、`available_tile_count`、`wall_remaining_count` |
| R6  | `type` や `round` のような汎用名を単独で使わない                                                                                                               | `foul_type`、`dora_type`、`stage_game_number`                 |
| R7  | 1 つの概念には、テーブルとビューを通して 1 つの語だけを使う。語は[用語集](#用語集)に従う                                                                       | `agari_tile`、`oya_player_id`、`kyotaku_count`                |
| R8  | `_event` はイベントの子テーブルだけに付ける                                                                                                                    | `agari_yaku`（`agari_yaku_event` にしない）                   |
| R9  | 牌を表す列は `tile` で終わる（複数の牌は `tiles`）                                                                                                             | `tile`、`agari_tile`、`dora_indicator_tile`、`waiting_tiles`  |
| R10 | 比率・平均の列は `<分子>_per_<分母>` にし、百分率なら末尾に `_percent` を付ける                                                                                | `agari_per_kyoku_percent`、`ura_dora_per_reach_agari`         |

### 補足

- **番号**: 何の中での番号かを名前に含める（`stage_game_number` はステージ内の通し番号、`day_game_number` はその日の何試合目か）。
- **R1 の内訳**: あがりの収入は `agari_points`（和了点）、`honba_points`（本場の加点）、`kyotaku_points`（回収した供託）に分けて持つ。合計が必要なら 3 つを足す。符号の有無など、名前で表しきれない違いは列の説明で補う。
- **R2 の例外**: 複合外部キーは、参照先の主キーと同じ列名をそのまま使う（`tenpai_agari_matrix(event_id, player_id)` → `player_tenpai_state(event_id, player_id)`）。参照先のテーブル名は列名に含めない。
- **R6 の例外**: 種別の判別に使う `event.type` と、場と局を表す `kyoku.round`（`1z1` など）は、麻雀の慣用に沿った名前なので単独名のまま残す。
- **R10 の分子・分母**: 集計ビューの件数列から `_count`（と `total_`）を除いた語にそろえる。`reach` だけではリーチ回数ともリーチあがり回数とも読めるため、`reach_agari_per_agari_percent` のように件数列と同じ語を使う。
- **R10 の例外は作らない**: 分母が一意に決まる指標（順位の指標など）にも `per_game` を付ける。「一意に決まるか」を判断する余地を残さないため。

## ビュー

| 種類                 | 形                         | 例                                                      |
| -------------------- | -------------------------- | ------------------------------------------------------- |
| 集計                 | `<対象>_<集計単位>_<内容>` | `player_season_stage_stats`、`team_season_stage_result` |
| 集計の元になる絶対値 | 末尾に `_base` を付ける    | `player_season_stage_stats_base`                        |

ビューの列:

| 種類       | 形                                                | 例                                           |
| ---------- | ------------------------------------------------- | -------------------------------------------- |
| 件数       | `<名詞>_count`。全体の件数は `total_<名詞>_count` | `agari_count`、`total_kyoku_count`           |
| 合計       | `<名詞>_total`                                    | `agari_points_total`、`dora_total`           |
| 比率・平均 | R10                                               | `dealin_per_kyoku_percent`、`dora_per_agari` |

複数ステージを合算する場合に正しく計算できるよう、比率・平均の元になる件数と合計は `_base` のビューに持たせる。

## 用語集

語を選ぶときの判断基準（上から優先）:

1. DB の用語と紛らわしくない（例: `parent` は親テーブルや親子関係と誤読されうる）。
2. 変更件数が少ない（すでに多く使われている語に寄せる）。
3. 日本語の質問と対応が付きやすい（例: 「親被り率」→ `oya_kaburi_per_oya_kyoku_percent`）。

| 概念                      | 語               | 備考                                                                                            |
| ------------------------- | ---------------- | ----------------------------------------------------------------------------------------------- |
| 局                        | `kyoku`          |                                                                                                 |
| 場と局（`1z1` は東 1 局） | `round`          | R6 の例外として単独名を使う                                                                     |
| 和了                      | `agari`          | `win` は使わない                                                                                |
| 親                        | `oya`            | `parent`、`dealer` は使わない                                                                   |
| 供託                      | `kyotaku`        | `reach_stick` は使わない。回収額は `kyotaku_points`                                             |
| 和了点                    | `agari_points`   | 本場・供託を含まない点数。`base_points`（英語の basic points と紛らわしい）や「素点」は使わない |
| 本場の加点                | `honba_points`   |                                                                                                 |
| テンパイ料                | `tenpai_points`  |                                                                                                 |
| M リーグの pt             | `league_points`  | 点棒単位の `*_points` と区別する                                                                |
| 本場                      | `honba`          |                                                                                                 |
| 放銃                      | `dealin`         |                                                                                                 |
| 被ツモ                    | `hitsumo`        |                                                                                                 |
| 立直                      | `reach`          | `riichi` は使わない                                                                             |
| 連荘                      | `renchan`        |                                                                                                 |
| 副露                      | `furo`           | チー・ポン・大明槓で晒した面子。暗槓を含まない                                                  |
| 鳴き                      | `call`           | 暗槓を含む（`call_count`、`is_called`）。`furo` とは別の概念                                    |
| 聴牌                      | `tenpai`         |                                                                                                 |
| 待ちの形                  | `waiting_type`   | 手牌全体の待ちは `waiting_type`、和了牌が入った面子の形は `agari_waiting_type`                  |
| 流局                      | `ryukyoku`       |                                                                                                 |
| 配牌                      | `haipai`         |                                                                                                 |
| 面前                      | `menzen`         |                                                                                                 |
| 役                        | `yaku`           |                                                                                                 |
| 牌                        | `tile`           | R9                                                                                              |
| ドラ表示牌                | `dora_indicator` | 牌の列は `dora_indicator_tile`                                                                  |
| 山                        | `wall`           |                                                                                                 |

新しい概念を追加するときは、判断基準に沿って語を決め、この表に追記する。

## インデックス・制約

インデックス名と制約名は、対象の列から機械的に決める（判断の余地を残さない）。
名前を手で付けず、テーブル名と対象列から組み立てる。

| 種類             | 形                                          | 例                                                                                 |
| ---------------- | ------------------------------------------- | ---------------------------------------------------------------------------------- |
| インデックス     | `idx_<テーブル名>_<対象列を順に>`           | `idx_game_player_result_team_id`、`idx_event_kyoku_id_type`                        |
| 一意インデックス | `idx_<テーブル名>_<対象列を順に>`           | `idx_game_season_stage_id_stage_game_number`                                       |
| CHECK            | `check_<テーブル名>_<式が参照する列を順に>` | `check_kyoku_honba_count`、`check_player_team_left_season_year_joined_season_year` |
| 単一列の UNIQUE  | `<テーブル名>_<列名>_unique`                | `player_name_unique`                                                               |
| 複合外部キー     | `fk_<テーブル名>_<参照先テーブル名>`        | `fk_tenpai_agari_matrix_player_tenpai_state`                                       |

- CHECK の名前には、式が参照する列をすべて、式に現れる順に含める。
- 列の順序や組み合わせが同じインデックスは作らない（名前が衝突し、冗長でもある）。
- CHECK の値リストは、列の型に合わせたリテラルで書く（整数列なら `IN (0, 1000)`、文字列列なら `IN ('omote', 'ura')`）。

## 型と単位

- 点棒（`score`、`*_points`）は整数で持つ。
- M リーグの pt（`league_points`、`penalty_league_points`、`league_points_total` など）は浮動小数点で持つため、合計すると丸め誤差が出る。集計結果は `ROUND(..., 1)` で丸める。集計ビューの pt の列は丸め済み。
- boolean は 0 / 1 の整数で持ち、`CHECK (... IN (0, 1))` を付ける。
- 日付は `YYYY-MM-DD` の文字列で持つ。
