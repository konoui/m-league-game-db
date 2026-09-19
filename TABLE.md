# データベースのテーブル、ビューとカラムの説明

<!-- TOC BEGIN -->

- [基本テーブル](#基本テーブル)
  - [league_season（リーグのシーズン）](#league_seasonリーグのシーズン)
  - [season_stage（シーズン内のステージ）](#season_stageシーズン内のステージ)
  - [team（チーム）](#teamチーム)
  - [player（プレイヤー）](#playerプレイヤー)
  - [player_team（プレイヤー・チーム関係）](#player_teamプレイヤーチーム関係)
- [試合・局テーブル](#試合局テーブル)
  - [game（試合）](#game試合)
  - [kyoku（局）](#kyoku局)
- [結果テーブル](#結果テーブル)
  - [game_player_result（試合単位のプレイヤーの結果）](#game_player_result試合単位のプレイヤーの結果)
  - [kyoku_player_result（局単位のプレイヤーの結果）](#kyoku_player_result局単位のプレイヤーの結果)
- [イベントテーブル](#イベントテーブル)
  - [event（イベント）](#eventイベント)
  - [各種イベント詳細テーブル](#各種イベント詳細テーブル)
    - [dora_indicator_event（ドラ表示牌イベント）](#dora_indicator_eventドラ表示牌イベント)
    - [haipai_event（配牌イベント）](#haipai_event配牌イベント)
    - [agari_event（ツモあがり、ロンあがりイベント）](#agari_eventツモあがりロンあがりイベント)
      - [agari_yaku（あがり時の役）](#agari_yakuあがり時の役)
    - [ryukyoku_event（流局イベント）](#ryukyoku_event流局イベント)
    - [ryukyoku_player（流局時のプレイヤー情報）](#ryukyoku_player流局時のプレイヤー情報)
    - [reach_event（リーチイベント）](#reach_eventリーチイベント)
    - [discard_event（打牌イベント）](#discard_event打牌イベント)
    - [draw_event（ツモイベント/牌をひくイベント）](#draw_eventツモイベント牌をひくイベント)
  - [鳴き関連テーブル](#鳴き関連テーブル)
    - [chi_event（チーイベント）](#chi_eventチーイベント)
    - [pon_event（ポンイベント）](#pon_eventポンイベント)
    - [ankan_event（暗槓イベント）](#ankan_event暗槓イベント)
    - [daiminkan_event（大明槓イベント）](#daiminkan_event大明槓イベント)
    - [shominkan_event（小明槓・カカンイベント）](#shominkan_event小明槓カカンイベント)
- [その他のテーブル](#その他のテーブル)
  - [yaku_name（役定義のテーブル）](#yaku_name役定義のテーブル)
  - [player_state（ある巡目におけるプレイヤーの状態）](#player_stateある巡目におけるプレイヤーの状態)
  - [player_tenpai_state（聴牌時のプレイヤーの状態）](#player_tenpai_state聴牌時のプレイヤーの状態)
  - [tenpai_agari_matrix（聴牌時のあがり可能性マトリックス）](#tenpai_agari_matrix聴牌時のあがり可能性マトリックス)
  - [tenpai_yaku（聴牌時のあがり役）](#tenpai_yaku聴牌時のあがり役)
  - [foul_play（反則行為・チョンボ）](#foul_play反則行為チョンボ)
- [集約テーブル（ビュー）](#集約テーブルビュー)
  - [team_season_stage_result（シーズンステージ単位のチームの結果）](#team_season_stage_resultシーズンステージ単位のチームの結果)
  - [player_season_stage_stats_base（シーズンステージ単位のプレイヤーの統計・絶対値）](#player_season_stage_stats_baseシーズンステージ単位のプレイヤーの統計絶対値)
  - [player_season_stage_stats（シーズンステージ単位のプレイヤーの統計）](#player_season_stage_statsシーズンステージ単位のプレイヤーの統計)

<!-- TOC END -->

## 基本テーブル

### league_season（リーグのシーズン）

> [!NOTE]
> end_year は start_year+1 となる。
> 2024-25 シーズンの場合 start_year が 2024、end_year が 2025 となる。

**主キー**: id

| カラム名   | データ型 | NULL 許可 | 説明        |
| ---------- | -------- | --------- | ----------- |
| id         | integer  | NO        | シーズン ID |
| start_year | integer  | NO        | 開始年      |
| end_year   | integer  | NO        | 終了年      |

### season_stage（シーズン内のステージ）

> [!NOTE]
> M リーグ公式は、レギュラーシーズン、セミファイナルシリーズ、ファイナルシリーズと呼ぶが、データベース内では年のシーズンと区別するためステージと呼ぶ。

**主キー**: id
**外部キー**: league_season_id -> league_season.id

| カラム名         | データ型                        | NULL 許可 | 説明                |
| ---------------- | ------------------------------- | --------- | ------------------- |
| id               | integer                         | NO        | シーズン ID         |
| league_season_id | integer                         | NO        | リーグのシーズン ID |
| stage            | ENUM(regular, semifinal, final) | NO        | シーズン種別        |

### team（チーム）

**主キー**: id

| カラム名           | データ型 | NULL 許可 | 説明         |
| ------------------ | -------- | --------- | ------------ |
| id                 | integer  | NO        | チーム ID    |
| name               | varchar  | NO        | チーム名     |
| joined_season_year | integer  | NO        | 参加開始年度 |

### player（プレイヤー）

> [!NOTE]
> name_furigana を使用してひらがなの名前から選手名/id を検索できる。

**主キー**: id

| カラム名           | データ型 | NULL 許可 | 説明                   |
| ------------------ | -------- | --------- | ---------------------- |
| id                 | integer  | NO        | プレイヤー ID          |
| name               | varchar  | NO        | プレイヤー名           |
| name_furigana      | varchar  | NO        | プレイヤー名のひらがな |
| joined_season_year | integer  | NO        | 参加開始年度           |

### player_team（プレイヤー・チーム関係）

> [!IMPORTANT]
> プレイヤーは移籍や再契約のため、年度によって別のチームに所属する可能性がある。
> SQL クエリでは考慮する必要がある。
> 試合・局の成績をチーム別に集計する場合は、このテーブルではなく game_player_result.team_id を使う。

**複合主キー**: team_id, player_id, joined_season_year
**外部キー**: player_id -> player.id, team_id -> team.id

| カラム名           | データ型 | NULL 許可 | 説明               |
| ------------------ | -------- | --------- | ------------------ |
| player_id          | integer  | NO        | プレイヤー ID      |
| team_id            | integer  | NO        | チーム ID          |
| joined_season_year | integer  | NO        | チーム参加開始年度 |
| left_season_year   | integer  | NO        | チーム離脱年度     |

## 試合・局テーブル

### game（試合）

**主キー**: id
**外部キー**: season_stage_id -> season_stage.id

| カラム名          | データ型 | NULL 許可 | 説明                                                                                      |
| ----------------- | -------- | --------- | ----------------------------------------------------------------------------------------- |
| id                | integer  | NO        | 試合 ID                                                                                   |
| season_stage_id   | integer  | NO        | シーズン内のステージの ID                                                                 |
| date              | date     | NO        | 試合日                                                                                    |
| day_game_number   | integer  | NO        | その日の何試合目か（基本的には 1、2）                                                     |
| stage_game_number | integer  | NO        | ステージ内で何試合目か（ステージごとに 1 から始まる通し番号。公式サイトの「N ラウンド」） |
| m_league_game_id  | varchar  | NO        | M リーグ公式が使用している試合 ID                                                         |

### kyoku（局）

**主キー**: id
**外部キー**: game_id -> game.id, oya_player_id -> player.id

| カラム名      | データ型                                       | NULL 許可 | 説明                                               |
| ------------- | ---------------------------------------------- | --------- | -------------------------------------------------- |
| id            | integer                                        | NO        | 局 ID                                              |
| game_id       | integer                                        | NO        | 試合 ID                                            |
| oya_player_id | integer                                        | NO        | 親プレイヤー ID                                    |
| round         | ENUM（1z1, 1z2, 1z3, 1z4, 2z1, 2z2, 2z3, 2z4） | NO        | 場                                                 |
| honba_count   | integer                                        | NO        | 本場数                                             |
| kyotaku_count | integer                                        | NO        | 局の開始時に持ち越されている供託（リーチ棒）の本数 |

## 結果テーブル

### game_player_result（試合単位のプレイヤーの結果）

> [!IMPORTANT]
> league_points / penalty_league_points は浮動小数点のため、合計すると -8.699999999999998 のような誤差が出る。集計結果は ROUND(..., 1) で丸める。
> 所属チームは team_id を使う。player_team を年度の範囲で結合する必要はない。

**複合主キー**: game_id, player_id
**外部キー**: game_id -> game.id, player_id -> player.id, team_id -> team.id

| カラム名              | データ型 | NULL 許可 | 説明                                      |
| --------------------- | -------- | --------- | ----------------------------------------- |
| game_id               | integer  | NO        | 試合 ID                                   |
| player_id             | integer  | NO        | プレイヤー ID                             |
| team_id               | integer  | NO        | この試合に出場したときの所属チーム ID     |
| score                 | integer  | NO        | 終了時の持ち点（スコア）                  |
| league_points         | numeric  | NO        | 順位点を加味した M リーグのポイント（pt） |
| penalty_league_points | numeric  | NO        | チョンボなど減点を表す反則ポイント（pt）  |
| rank                  | integer  | NO        | 終了時の順位                              |

### kyoku_player_result（局単位のプレイヤーの結果）

**複合主キー**: kyoku_id, player_id
**外部キー**: kyoku_id -> kyoku.id, player_id -> player.id

| カラム名    | データ型             | NULL 許可 | 説明             |
| ----------- | -------------------- | --------- | ---------------- |
| kyoku_id    | integer              | NO        | 局 ID            |
| player_id   | integer              | NO        | プレイヤー ID    |
| score       | integer              | NO        | 局終了時のスコア |
| player_wind | ENUM(1z, 2z, 3z, 4z) | NO        | 自風             |
| rank        | integer              | NO        | 局終了時の順位   |

## イベントテーブル

### event（イベント）

> [!NOTE]
> 具体的なイベントの内容は、各種イベントテーブルと結合して参照する。

**主キー**: id
**外部キー**: kyoku_id -> kyoku.id

| カラム名    | データ型                                                                                              | NULL 許可 | 説明             |
| ----------- | ----------------------------------------------------------------------------------------------------- | --------- | ---------------- |
| id          | integer                                                                                               | NO        | イベント ID      |
| kyoku_id    | integer                                                                                               | NO        | 局 ID            |
| type        | ENUM(haipai, draw, discard,ron,tsumo,reach,pon,chi,daiminkan,shominkan,ankan,dora_indicator,ryukyoku) | NO        | イベント種別     |
| event_order | integer                                                                                               | NO        | イベント順序番号 |

### 各種イベント詳細テーブル

#### dora_indicator_event（ドラ表示牌イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id

| カラム名            | データ型         | NULL 許可 | 説明                       |
| ------------------- | ---------------- | --------- | -------------------------- |
| event_id            | integer          | NO        | イベント ID                |
| dora_type           | ENUM(omote, ura) | NO        | ドラ種別（表ドラ・裏ドラ） |
| dora_indicator_tile | varchar          | NO        | ドラ表示牌                 |
| dora_tile           | varchar          | NO        | ドラ牌                     |

#### haipai_event（配牌イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名          | データ型 | NULL 許可 | 説明                                                    |
| ----------------- | -------- | --------- | ------------------------------------------------------- |
| event_id          | integer  | NO        | イベント ID                                             |
| actor_player_id   | integer  | NO        | 配牌を受け取ったプレイヤー ID                           |
| hand              | varchar  | NO        | 配牌時の手牌                                            |
| is_tenho_possible | boolean  | NO        | 配牌時に天和チャンスであるか（親でシャンテン数が 0 か） |
| is_chiho_possible | boolean  | NO        | 配牌時に地和チャンスであるか（子でシャンテン数が 0 か） |

#### agari_event（ツモあがり、ロンあがりイベント）

> [!IMPORTANT]
> 役満の集計には必ず is_yakuman を使う。M リーグは数え役満がないため、han >= 13 でも役満ではない（三倍満の）あがりがあり、han で数えると多くなる。

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id, target_player_id -> player.id

| カラム名           | データ型                                             | NULL 許可 | 説明                                                                                                                                                           |
| ------------------ | ---------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| event_id           | integer                                              | NO        | イベント ID                                                                                                                                                    |
| actor_player_id    | integer                                              | NO        | あがったプレイヤー ID                                                                                                                                          |
| target_player_id   | integer                                              | YES       | 放銃したプレイヤー ID（ツモあがりの場合は null）                                                                                                               |
| agari_points       | integer                                              | NO        | 和了点（本場・供託を含まない。満貫なら 8000）                                                                                                                  |
| honba_points       | integer                                              | NO        | 本場の加点（本場数 × 300）                                                                                                                                     |
| kyotaku_points     | integer                                              | NO        | 回収した供託（リーチ棒の本数 × 1000）。その局で自分が出したリーチ棒も含む                                                                                      |
| revenue_points     | integer                                              | NO        | あがりで得た点数の合計（= agari_points + honba_points + kyotaku_points）。生成列なので内訳と必ず一致する                                                       |
| agari_tile         | varchar                                              | NO        | ロン（放銃）牌もしくはツモあがり牌                                                                                                                             |
| agari_waiting_type | ENUM(両面、単騎、カンチャン、ペンチャン、シャンポン) | NO        | 和了牌が入った面子の形。手牌全体の待ちの形は player_tenpai_state.waiting_type で、そちらは複合形・ノベタン・亜両面も取る（粒度が違うので一致しないことがある） |
| fu                 | integer                                              | NO        | 合計の符                                                                                                                                                       |
| han                | integer                                              | NO        | 合計の翻数（役満判定には使わない。is_yakuman を参照する）                                                                                                      |
| is_called          | boolean                                              | NO        | 鳴いたあがりか（暗槓を含む）                                                                                                                                   |
| is_menzen          | boolean                                              | NO        | 面前のあがりか                                                                                                                                                 |
| is_yakuman         | boolean                                              | NO        | 役満か（han >= 13 とは一致しない。数え役満がないルールのため）                                                                                                 |
| description        | varchar                                              | NO        | 役と点数の説明                                                                                                                                                 |

##### agari_yaku（あがり時の役）

**複合主キー**: agari_event_id, yaku_name_id
**外部キー**: agari_event_id -> agari_event.event_id, yaku_name_id -> yaku_name.id

| カラム名       | データ型 | NULL 許可 | 説明                  |
| -------------- | -------- | --------- | --------------------- |
| agari_event_id | integer  | NO        | あがり時のイベント ID |
| yaku_name_id   | integer  | NO        | 役の名前 ID           |
| han            | integer  | NO        | 役の翻数              |

#### ryukyoku_event（流局イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id

| カラム名 | データ型        | NULL 許可 | 説明        |
| -------- | --------------- | --------- | ----------- |
| event_id | integer         | NO        | イベント ID |
| reason   | ENUM(end_kyoku) | NO        | 流局理由    |

#### ryukyoku_player（流局時のプレイヤー情報）

**複合主キー**: ryukyoku_event_id, player_id
**外部キー**: ryukyoku_event_id -> ryukyoku_event.event_id, player_id -> player.id

| カラム名          | データ型 | NULL 許可 | 説明                                          |
| ----------------- | -------- | --------- | --------------------------------------------- |
| ryukyoku_event_id | integer  | NO        | 流局時のイベント ID                           |
| player_id         | integer  | NO        | プレイヤー ID                                 |
| is_tenpai         | boolean  | NO        | 聴牌か（false はノーテンを表す）              |
| tenpai_points     | integer  | NO        | 聴牌・ノーテン時の点数移動（-3000 から 3000） |

#### reach_event（リーチイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名        | データ型 | NULL 許可 | 説明                                                                               |
| --------------- | -------- | --------- | ---------------------------------------------------------------------------------- |
| event_id        | integer  | NO        | イベント ID                                                                        |
| actor_player_id | integer  | NO        | リーチプレイヤー ID                                                                |
| is_accepted     | boolean  | NO        | リーチ宣言が受け入れられたかのフラグ。false であればリーチ宣言で放銃（ロン）を表す |

#### discard_event（打牌イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名             | データ型 | NULL 許可 | 説明              |
| -------------------- | -------- | --------- | ----------------- |
| event_id             | integer  | NO        | イベント ID       |
| actor_player_id      | integer  | NO        | 打牌プレイヤー ID |
| tile                 | varchar  | NO        | 打牌              |
| is_reach_declaration | boolean  | NO        | リーチ宣言フラグ  |
| is_tsumogiri         | boolean  | NO        | ツモ切りフラグ    |

#### draw_event（ツモイベント/牌をひくイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名             | データ型 | NULL 許可 | 説明                                                                                |
| -------------------- | -------- | --------- | ----------------------------------------------------------------------------------- |
| event_id             | integer  | NO        | イベント ID                                                                         |
| actor_player_id      | integer  | NO        | ツモしたプレイヤー ID                                                               |
| tile                 | varchar  | NO        | ツモした牌                                                                          |
| is_rinshan           | boolean  | NO        | 嶺上フラグ                                                                          |
| wall_remaining_count | integer  | NO        | このツモ後に山に残っているツモ可能な枚数（王牌は含まない。69 から始まり流局時は 0） |

### 鳴き関連テーブル

#### chi_event（チーイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id, target_player_id -> player.id

| カラム名             | データ型 | NULL 許可 | 説明                                                                                                                                                         |
| -------------------- | -------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| event_id             | integer  | NO        | イベント ID                                                                                                                                                  |
| actor_player_id      | integer  | NO        | チーしたプレイヤー ID                                                                                                                                        |
| target_player_id     | integer  | NO        | 牌を捨てたプレイヤー ID                                                                                                                                      |
| tile                 | varchar  | NO        | チーした牌                                                                                                                                                   |
| block                | varchar  | NO        | 鳴いた後の牌のブロック                                                                                                                                       |
| furo_count           | integer  | NO        | この鳴きの後の副露数（1 副露目なら 1。暗槓は含めない）                                                                                                       |
| before_shanten_count | integer  | NO        | 鳴く直前（13 枚）の一般形シャンテン数。鳴いた後は七対子・国士が成立しないため一般形で数える                                                                  |
| after_shanten_count  | integer  | NO        | 面子を晒した直後、打牌より前の一般形シャンテン数。14 枚相当なので最善の打牌をした場合の値になり、実際の打牌後の値以下になる。聴牌から和了牌を鳴いた場合は -1 |

#### pon_event（ポンイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id, target_player_id -> player.id

| カラム名             | データ型 | NULL 許可 | 説明                                                                                                                                                         |
| -------------------- | -------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| event_id             | integer  | NO        | イベント ID                                                                                                                                                  |
| actor_player_id      | integer  | NO        | ポンしたプレイヤー ID                                                                                                                                        |
| target_player_id     | integer  | NO        | 牌を捨てたプレイヤー ID                                                                                                                                      |
| block                | varchar  | NO        | 鳴いた後の牌のブロック                                                                                                                                       |
| tile                 | varchar  | NO        | ポンした牌                                                                                                                                                   |
| furo_count           | integer  | NO        | この鳴きの後の副露数（1 副露目なら 1。暗槓は含めない）                                                                                                       |
| before_shanten_count | integer  | NO        | 鳴く直前（13 枚）の一般形シャンテン数。鳴いた後は七対子・国士が成立しないため一般形で数える                                                                  |
| after_shanten_count  | integer  | NO        | 面子を晒した直後、打牌より前の一般形シャンテン数。14 枚相当なので最善の打牌をした場合の値になり、実際の打牌後の値以下になる。聴牌から和了牌を鳴いた場合は -1 |

#### ankan_event（暗槓イベント）

> [!NOTE]
> 暗槓は副露に数えないため furo_count を持たない（鳴いた回数は player_state.call_count に含まれる）。

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名             | データ型 | NULL 許可 | 説明                                           |
| -------------------- | -------- | --------- | ---------------------------------------------- |
| event_id             | integer  | NO        | イベント ID                                    |
| actor_player_id      | integer  | NO        | カンしたプレイヤー ID                          |
| tile                 | varchar  | NO        | カンをした牌                                   |
| block                | varchar  | NO        | 鳴いた後の牌のブロック                         |
| before_shanten_count | integer  | NO        | 槓する直前の一般形シャンテン数                 |
| after_shanten_count  | integer  | NO        | 槓した直後、嶺上ツモより前の一般形シャンテン数 |

#### daiminkan_event（大明槓イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id, target_player_id -> player.id

| カラム名             | データ型 | NULL 許可 | 説明                                                                                        |
| -------------------- | -------- | --------- | ------------------------------------------------------------------------------------------- |
| event_id             | integer  | NO        | イベント ID                                                                                 |
| actor_player_id      | integer  | NO        | カンしたプレイヤー ID                                                                       |
| target_player_id     | integer  | NO        | 牌を捨てたプレイヤー ID                                                                     |
| tile                 | varchar  | NO        | カンをした牌                                                                                |
| block                | varchar  | NO        | 鳴いた後の牌のブロック                                                                      |
| furo_count           | integer  | NO        | この鳴きの後の副露数（1 副露目なら 1。暗槓は含めない）                                      |
| before_shanten_count | integer  | NO        | 鳴く直前（13 枚）の一般形シャンテン数。鳴いた後は七対子・国士が成立しないため一般形で数える |
| after_shanten_count  | integer  | NO        | 面子を晒した直後、嶺上ツモより前の一般形シャンテン数                                        |

#### shominkan_event（小明槓・カカンイベント）

> [!NOTE]
> 加槓は元のポンのまま数えるため副露数が変わらず、furo_count を持たない。

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名             | データ型 | NULL 許可 | 説明                                           |
| -------------------- | -------- | --------- | ---------------------------------------------- |
| event_id             | integer  | NO        | イベント ID                                    |
| actor_player_id      | integer  | NO        | カンしたプレイヤー ID                          |
| tile                 | varchar  | NO        | カンをした牌                                   |
| block                | varchar  | NO        | 鳴いた後の牌のブロック                         |
| before_shanten_count | integer  | NO        | 槓する直前の一般形シャンテン数                 |
| after_shanten_count  | integer  | NO        | 槓した直後、嶺上ツモより前の一般形シャンテン数 |

## その他のテーブル

### yaku_name（役定義のテーブル）

> [!NOTE]
> name_furigana を使用して役名をカタカナ名で検索できる。

**主キー**: id

| カラム名      | データ型 | NULL 許可 | 説明                                                                 |
| ------------- | -------- | --------- | -------------------------------------------------------------------- |
| id            | integer  | NO        | ID                                                                   |
| name          | varchar  | NO        | 役の名前                                                             |
| name_furigana | varchar  | NO        | カタカナの役の名前                                                   |
| is_yakuman    | boolean  | NO        | 役満の役か。あるあがりが役満だったかは agari_event.is_yakuman を使う |

### player_state（ある巡目におけるプレイヤーの状態）

> [!NOTE]
> event_id よりどのイベント時の状態か確認できる。
> turn_number からある巡目の情報を確認できる。0 は配牌時の状態を表す。
> 特別な要件がなければシャンテン数には shanten_count を使用する。

**複合主キー**: event_id, player_id
**外部キー**: event_id -> event.id, player_id -> player.id

| カラム名                       | データ型 | NULL 許可 | 説明                                                                                                                                         |
| ------------------------------ | -------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| event_id                       | integer  | NO        | イベント ID                                                                                                                                  |
| player_id                      | integer  | NO        | プレイヤー ID                                                                                                                                |
| hand                           | varchar  | NO        | 手牌                                                                                                                                         |
| called_blocks                  | varchar  | NO        | 鳴いて晒した牌のブロック（,区切り）                                                                                                          |
| shanten_count                  | integer  | NO        | シャンテン数（標準形、七対子、国士無双のシャンテン数の内最小の値）                                                                           |
| standard_type_shanten_count    | integer  | NO        | 標準形のシャンテン数                                                                                                                         |
| seven_pairs_shanten_count      | integer  | YES       | 七対子のシャンテン数（鳴いている場合 null となる）                                                                                           |
| thirteen_orphans_shanten_count | integer  | YES       | 国士無双のシャンテン数（鳴いている場合 null となる）                                                                                         |
| is_reached                     | boolean  | NO        | リーチ状態か                                                                                                                                 |
| is_furiten                     | boolean  | NO        | フリテン状態か                                                                                                                               |
| turn_number                    | integer  | NO        | 何巡目のプレイヤーの情報かを表す（プレイヤーの打牌回数）。0 は配牌時の情報                                                                   |
| call_count                     | integer  | NO        | 鳴いた回数、ただし暗槓を含む                                                                                                                 |
| furo_count                     | integer  | NO        | 副露数。チー・ポン・大明槓で晒した面子の数で、暗槓は含めず加槓は元のポンのまま数える（集計ビューの furo_count は副露した局数で単位が異なる） |
| is_menzen                      | boolean  | NO        | 面前か                                                                                                                                       |

### player_tenpai_state（聴牌時のプレイヤーの状態）

> [!NOTE]
> event_id よりどのイベント時の状態か確認できる。打牌・配牌に加えて流局時にも記録するが、流局時は手牌が開示される聴牌者のみで、ノーテン者の行は作らない（聴牌かどうかは ryukyoku_player.is_tenpai を参照する）。

**複合主キー**: event_id, player_id
**外部キー**: event_id -> event.id, player_id -> player.id

| カラム名                  | データ型                                                                       | NULL 許可 | 説明                                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------ | --------- | ---------------------------------------------------------------------------------------------------------- |
| event_id                  | integer                                                                        | NO        | イベント ID                                                                                                |
| player_id                 | integer                                                                        | NO        | プレイヤー ID                                                                                              |
| waiting_tiles             | varchar                                                                        | NO        | 待ち牌                                                                                                     |
| waiting_type              | ENUM(単騎、シャンポン、両面、カンチャン、ペンチャン、ノベタン、亜両面、複合形) | NO        | 待ちのタイプ                                                                                               |
| tile_type_count           | integer                                                                        | NO        | 待ち牌の種類                                                                                               |
| ideal_tile_count          | integer                                                                        | NO        | 論理的な（平面の）待ち牌の数                                                                               |
| available_tile_count      | integer                                                                        | NO        | 神目線の待ち牌の数（山に残っている枚数。流局時点では生牌の山が尽きているため、王牌に残っていた枚数を表す） |
| discarded_tile_count      | integer                                                                        | NO        | 捨て牌にある待ち牌の数                                                                                     |
| dora_indicator_tile_count | integer                                                                        | NO        | ドラ表示牌にある待ち牌の数                                                                                 |

### tenpai_agari_matrix（聴牌時のあがり可能性マトリックス）

> [!NOTE]
> 聴牌時のイベントに対して、各待ち牌ごとのロン・ツモあがりおよび役の可能性を記録する。役がつかず和了できない牌は行を作らないため、あがれる牌かどうかは行の有無で判定する。含めるのは「その牌で和了した時点で確定する役」だけで、立直・ダブル立直・ドラ・赤ドラ・カンドラは含め、和了の時点に依存する。一発・海底摸月・河底撈魚・嶺上開花・槍槓と、局中は不可知な裏ドラは含めない。
> 各行は (event_id, player_id) で player_tenpai_state の 1 行に対応する。player_tenpai_state と結合するときは event_id と player_id の両方で結合する。
> 流局後は和了し得ないため流局イベントには作らない。流局時の聴牌者の待ち牌ごとの打点を調べる場合は、流局イベントと同じ kyoku_id で、そのプレイヤー（discard_event.actor_player_id）の event_order が最大の打牌イベントを探し、その event.id と player_id で結合する。流局時の手牌は最後の打牌後の手牌と同じなので待ち牌は一致する。ただし available_tile_count は打牌時点の値で、最後の打牌より後に増えたカンドラは反映されていない。

**主キー**: id
**外部キー**: (event_id, player_id) -> player_tenpai_state(event_id, player_id)

| カラム名             | データ型 | NULL 許可 | 説明                                         |
| -------------------- | -------- | --------- | -------------------------------------------- |
| id                   | integer  | NO        | ID                                           |
| event_id             | integer  | NO        | 聴牌時のイベント ID（配牌・打牌イベント）    |
| player_id            | integer  | NO        | 聴牌しているプレイヤー ID                    |
| waiting_tile         | varchar  | NO        | 待ち牌                                       |
| available_tile_count | integer  | NO        | あがれる牌の残り枚数（神目線）               |
| is_ron_agari         | boolean  | NO        | ロンあがり想定か（false はツモあがりを表す） |

### tenpai_yaku（聴牌時のあがり役）

> [!NOTE]
> tenpai_agari_matrix と結合して、各待ち牌であがった場合の役を参照できる。

**複合主キー**: tenpai_agari_matrix_id, yaku_name_id
**外部キー**: tenpai_agari_matrix_id -> tenpai_agari_matrix.id, yaku_name_id -> yaku_name.id

| カラム名               | データ型 | NULL 許可 | 説明                        |
| ---------------------- | -------- | --------- | --------------------------- |
| tenpai_agari_matrix_id | integer  | NO        | あがり可能性マトリックス ID |
| yaku_name_id           | integer  | NO        | 役の名前 ID                 |
| han                    | integer  | NO        | 役の翻数                    |

### foul_play（反則行為・チョンボ）

**主キー**: id
**外部キー**: kyoku_id -> kyoku.id, actor_player_id -> player.id

| カラム名              | データ型                                                         | NULL 許可 | 説明                                                    |
| --------------------- | ---------------------------------------------------------------- | --------- | ------------------------------------------------------- |
| id                    | integer                                                          | NO        | ID                                                      |
| kyoku_id              | integer                                                          | NO        | 局 ID                                                   |
| actor_player_id       | integer                                                          | NO        | 反則・チョンボを行ったプレイヤー ID                     |
| penalty_league_points | numeric                                                          | NO        | 反則・チョンボのペナルティポイント（pt。デフォルト: 0） |
| description           | varchar                                                          | NO        | 反則・チョンボの詳細説明                                |
| foul_type             | ENUM(ノーテンリーチ, 誤ポン, 誤チー, 少牌, 多牌, 誤ツモ, 誤ロン) | NO        | 反則・チョンボの種類                                    |
| is_restarted          | boolean                                                          | NO        | その局をやりなおし                                      |

## 集約テーブル（ビュー）

### team_season_stage_result（シーズンステージ単位のチームの結果）

> [!NOTE]
> ビュー

| カラム名            | データ型                        | NULL 許可 | 説明                                                                                                                                                                       |
| ------------------- | ------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| team_id             | integer                         | NO        | ID                                                                                                                                                                         |
| team_name           | varchar                         | NO        | チーム名                                                                                                                                                                   |
| season_start_year   | integer                         | NO        | シーズンの開始年度                                                                                                                                                         |
| season_end_year     | integer                         | NO        | シーズンの終了年度                                                                                                                                                         |
| stage               | ENUM(regular, semifinal, final) | NO        | シーズン種別                                                                                                                                                               |
| stage_league_points | numeric                         | NO        | チームごとの順位点を加味した pt（そのステージ分のみ。小数第 1 位で丸め済み）                                                                                               |
| final_league_points | numeric                         | NO        | stage_league_points に regular, semifinal からの持ち越しポイントを加算した値。この値を使用して優勝を決定する（持ち越しで 0.025pt 単位になりうるため小数第 3 位で丸め済み） |

### player_season_stage_stats_base（シーズンステージ単位のプレイヤーの統計・絶対値）

> [!NOTE]
> ビュー。player_season_stage_stats の元となる絶対値ビュー。
> ステージをまたいだ集計など、パーセントでは正確に算出できない集計に使用する。
> 複数ステージを合算する場合は agari_count / total_kyoku_count などの絶対値を SUM してからパーセントを計算する。

| カラム名                                       | データ型                        | NULL 許可 | 説明                                                                                                                                                                      |
| ---------------------------------------------- | ------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| season_start_year                              | integer                         | NO        | シーズン開始年                                                                                                                                                            |
| stage                                          | ENUM(regular, semifinal, final) | NO        | ステージ                                                                                                                                                                  |
| player_name                                    | text                            | NO        | プレイヤー名                                                                                                                                                              |
| team_name                                      | text                            | NO        | チーム名                                                                                                                                                                  |
| total_kyoku_count                              | integer                         | NO        | 総局数                                                                                                                                                                    |
| total_game_count                               | integer                         | NO        | 総ゲーム数                                                                                                                                                                |
| agari_count                                    | integer                         | NO        | あがり回数                                                                                                                                                                |
| agari_points_total                             | integer                         | YES       | あがり打点の合計（本場・リーチ棒を含まない）                                                                                                                              |
| tsumo_agari_count                              | integer                         | NO        | ツモあがり回数                                                                                                                                                            |
| dealin_count                                   | integer                         | NO        | 放銃回数                                                                                                                                                                  |
| dealin_points_total                            | integer                         | YES       | 放銃打点の合計                                                                                                                                                            |
| hitsumo_count                                  | integer                         | NO        | 被ツモ回数（他プレイヤーのツモ上がりで失点した回数）                                                                                                                      |
| reach_count                                    | integer                         | NO        | 立直回数（リーチ宣言が受理された回数）                                                                                                                                    |
| reach_agari_count                              | integer                         | NO        | リーチあがり回数                                                                                                                                                          |
| furo_agari_count                               | integer                         | NO        | 副露あがり回数                                                                                                                                                            |
| reach_dealin_count                             | integer                         | NO        | リーチ後放銃回数                                                                                                                                                          |
| reach_declare_dealin_count                     | integer                         | NO        | リーチ宣言時放銃回数（リーチ宣言が受理されなかった回数）                                                                                                                  |
| furo_count                                     | integer                         | NO        | 副露局数                                                                                                                                                                  |
| ryukyoku_count                                 | integer                         | NO        | 流局回数                                                                                                                                                                  |
| tenpai_count                                   | integer                         | NO        | 流局時聴牌回数                                                                                                                                                            |
| tenpai_points_total                            | integer                         | YES       | 流局時テンパイ料収支の合計                                                                                                                                                |
| dora_total                                     | integer                         | NO        | あがり時ドラ枚数合計（赤、裏除く）                                                                                                                                        |
| aka_dora_total                                 | integer                         | NO        | あがり時赤ドラ枚数合計                                                                                                                                                    |
| ura_dora_total                                 | integer                         | NO        | あがり時裏ドラ枚数合計                                                                                                                                                    |
| ura_dora_agari_count                           | integer                         | NO        | 裏ドラが乗ったあがり回数                                                                                                                                                  |
| renchan_count                                  | integer                         | NO        | 連荘回数（親番であがりまたは聴牌流局した局数）                                                                                                                            |
| oya_kyoku_count                                | integer                         | NO        | 親局数                                                                                                                                                                    |
| oya_kaburi_count                               | integer                         | NO        | 親被り回数（親番でツモあがりされた回数）                                                                                                                                  |
| itai_oya_kaburi_count                          | integer                         | NO        | 親の時に満貫以上の親被りをした回数                                                                                                                                        |
| itai_oya_kaburi_points_total                   | integer                         | YES       | 親の時に満貫以上の親被りをしたポイントの合計                                                                                                                              |
| carryover_kyotaku_points_total                 | integer                         | NO        | あがった局に持ち越されていた供託（リーチ棒）の合計                                                                                                                        |
| kyotaku_points_excluding_own_reach_total       | integer                         | NO        | 回収した供託の合計から、その局で自分が出したリーチ棒（戻ってくるだけで増えていない分）を差し引いた値                                                                      |
| kyotaku_honba_points_excluding_own_reach_total | integer                         | NO        | あがりで得た供託と本場の加点の合計（その局で自分が出したリーチ棒は差し引く）。和了点を除いた収入にあたる。= kyotaku_points_excluding_own_reach_total + honba_points_total |
| honba_points_total                             | integer                         | NO        | あがり時の本場の加点の合計                                                                                                                                                |
| rank1_count                                    | integer                         | NO        | 一位回数                                                                                                                                                                  |
| rank2_count                                    | integer                         | NO        | 二位回数                                                                                                                                                                  |
| rank3_count                                    | integer                         | NO        | 三位回数                                                                                                                                                                  |
| rank4_count                                    | integer                         | NO        | 四位回数                                                                                                                                                                  |
| best_score                                     | integer                         | YES       | ベストスコア                                                                                                                                                              |
| league_points_total                            | numeric                         | YES       | 順位点を加味した pt の累計                                                                                                                                                |

### player_season_stage_stats（シーズンステージ単位のプレイヤーの統計）

> [!NOTE]
> ビュー。player_season_stage_stats_base を元にパーセントや平均を算出したビュー。

| カラム名                                       | データ型                        | NULL 許可 | 説明                                                                                                                                                                      |
| ---------------------------------------------- | ------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| season_start_year                              | integer                         | NO        | シーズン開始年                                                                                                                                                            |
| stage                                          | ENUM(regular, semifinal, final) | NO        | ステージ                                                                                                                                                                  |
| player_name                                    | text                            | NO        | プレイヤー名                                                                                                                                                              |
| team_name                                      | text                            | NO        | チーム名                                                                                                                                                                  |
| total_game_count                               | integer                         | NO        | 総ゲーム数                                                                                                                                                                |
| agari_per_kyoku_percent                        | numeric                         | YES       | あがり率（パーセント）                                                                                                                                                    |
| tsumo_agari_per_agari_percent                  | numeric                         | YES       | ツモあがり率（パーセント）                                                                                                                                                |
| reach_agari_per_agari_percent                  | numeric                         | YES       | リーチあがり率（パーセント）                                                                                                                                              |
| furo_agari_per_agari_percent                   | numeric                         | YES       | 副露あがり率（パーセント）                                                                                                                                                |
| dama_agari_per_agari_percent                   | numeric                         | YES       | ダマあがり率（パーセント）                                                                                                                                                |
| dealin_per_kyoku_percent                       | numeric                         | YES       | 放銃率（パーセント）                                                                                                                                                      |
| hitsumo_per_kyoku_percent                      | numeric                         | YES       | 被ツモ率（パーセント）                                                                                                                                                    |
| furo_per_kyoku_percent                         | numeric                         | YES       | 副露率（パーセント）                                                                                                                                                      |
| reach_per_kyoku_percent                        | numeric                         | YES       | 立直率（パーセント）                                                                                                                                                      |
| reach_agari_per_reach_percent                  | numeric                         | YES       | 立直成立後のあがり率（パーセント）                                                                                                                                        |
| ryukyoku_per_kyoku_percent                     | numeric                         | YES       | 流局率（パーセント）                                                                                                                                                      |
| tenpai_per_ryukyoku_percent                    | numeric                         | YES       | 流局時聴牌率（パーセント）                                                                                                                                                |
| tenpai_points_per_ryukyoku                     | numeric                         | YES       | 流局 1 回あたりのテンパイ料の平均                                                                                                                                         |
| dora_per_agari                                 | numeric                         | YES       | あがり時平均ドラ数（赤、裏除く）                                                                                                                                          |
| aka_dora_per_agari                             | numeric                         | YES       | あがり時平均赤ドラ数                                                                                                                                                      |
| ura_dora_per_reach_agari                       | numeric                         | YES       | あがり時平均裏ドラ数                                                                                                                                                      |
| ura_dora_agari_per_reach_agari_percent         | numeric                         | YES       | あがり時裏ドラが乗った率（パーセント）                                                                                                                                    |
| all_dora_per_agari                             | numeric                         | YES       | あがり時平均全ドラ数                                                                                                                                                      |
| renchan_per_oya_kyoku_percent                  | numeric                         | YES       | 連荘率                                                                                                                                                                    |
| oya_kaburi_per_oya_kyoku_percent               | numeric                         | YES       | 親被り率                                                                                                                                                                  |
| itai_oya_kaburi_per_oya_kaburi_percent         | numeric                         | YES       | 痛い親被り率（親被り中のパーセント）                                                                                                                                      |
| reach_dealin_per_reach_percent                 | numeric                         | YES       | リーチ後放銃率（立直成立後のパーセント）                                                                                                                                  |
| reach_declare_dealin_count                     | integer                         | NO        | リーチ宣言時放銃回数                                                                                                                                                      |
| carryover_kyotaku_points_total                 | integer                         | NO        | あがった局に持ち越されていた供託（リーチ棒）の合計                                                                                                                        |
| kyotaku_points_excluding_own_reach_total       | integer                         | NO        | 回収した供託の合計から、その局で自分が出したリーチ棒（戻ってくるだけで増えていない分）を差し引いた値                                                                      |
| kyotaku_honba_points_excluding_own_reach_total | integer                         | NO        | あがりで得た供託と本場の加点の合計（その局で自分が出したリーチ棒は差し引く）。和了点を除いた収入にあたる。= kyotaku_points_excluding_own_reach_total + honba_points_total |
| honba_points_total                             | integer                         | NO        | あがり時の本場の加点の合計                                                                                                                                                |
| rank1_count                                    | integer                         | NO        | 一位回数                                                                                                                                                                  |
| rank2_count                                    | integer                         | NO        | 二位回数                                                                                                                                                                  |
| rank3_count                                    | integer                         | NO        | 三位回数                                                                                                                                                                  |
| rank4_count                                    | integer                         | NO        | 四位回数                                                                                                                                                                  |
| top_per_game_percent                           | numeric                         | YES       | トップ率（パーセント）                                                                                                                                                    |
| top2_per_game_percent                          | numeric                         | YES       | 連対率（パーセント）                                                                                                                                                      |
| avoid_last_per_game_percent                    | numeric                         | YES       | ラス回避率（パーセント）                                                                                                                                                  |
| best_score                                     | integer                         | YES       | ベストスコア                                                                                                                                                              |
| agari_points_per_agari                         | integer                         | YES       | 平均打点                                                                                                                                                                  |
| dealin_points_per_dealin                       | integer                         | YES       | 放銃平均打点                                                                                                                                                              |
| league_points_total                            | numeric                         | YES       | 順位点を加味した pt の累計                                                                                                                                                |
| yokomove_per_kyoku_percent                     | numeric                         | YES       | 横移動率（他者がロンあがりし自分が無関係な局のパーセント）                                                                                                                |
