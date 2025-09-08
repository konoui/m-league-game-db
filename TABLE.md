# データベースのテーブル、ビューとカラムの説明

## 基本テーブル

### league_season（リーグのシーズン）

> [!NOTE]
> end_year は start_year+1 となる。
> 2024-25 シーズンと言えば、start_year が 2024、end_year が 2025 となる。

**主キー**: id

| カラム名   | データ型 | NULL 許可 | 説明        |
| ---------- | -------- | --------- | ----------- |
| id         | integer  | NO        | シーズン ID |
| start_year | integer  | NO        | 開始年      |
| end_year   | integer  | NO        | 終了年      |

### season_stage（シーズン内のステージ）

> [!NOTE]
> M リーグ公式は、レギュラーシーズン、セファイナルシリーズ、ファイナルシリーズと呼ぶが、データベース内では年のシーズン特別するためステージと呼ぶ。

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

> [!NOTE]
> プレイヤーは移籍や再契約のため、年度によって別のチームに所属する可能性がある。

**複合主キー**: player_id, team_id
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

| カラム名         | データ型 | NULL 許可 | 説明                                                |
| ---------------- | -------- | --------- | --------------------------------------------------- |
| id               | integer  | NO        | 試合 ID                                             |
| season_stage_id  | integer  | NO        | シーズン内のステージの ID                           |
| date             | date     | NO        | 試合日                                              |
| match_number     | integer  | NO        | その日の第何試合かを表す試合番号（基本的には 1、2） |
| round_number     | integer  | NO        | ラウンド番号（シーズン内で単調増加する）            |
| m_league_game_id | varchar  | NO        | M リーグ公式が使用している試合 ID                   |

### kyoku（局）

**主キー**: id
**外部キー**: game_id -> game.id, parent_player_id -> player.id

| カラム名          | データ型                                       | NULL 許可 | 説明            |
| ----------------- | ---------------------------------------------- | --------- | --------------- |
| id                | integer                                        | NO        | 局 ID           |
| game_id           | integer                                        | NO        | 試合 ID         |
| parent_player_id  | integer                                        | NO        | 親プレイヤー ID |
| round             | ENUM（1z1, 1z2, 1z3, 1z4, 2z1, 2z2, 2z3, 2z4） | NO        | 場              |
| honba_count       | integer                                        | NO        | 本場数          |
| reach_stick_count | integer                                        | NO        | リーチ棒数      |

## 結果テーブル

### game_player_result（試合単位のプレイヤーの結果）

**主キー**: id
**外部キー**: game_id -> game.id, player_id -> player.id

| カラム名       | データ型 | NULL 許可 | 説明                               |
| -------------- | -------- | --------- | ---------------------------------- |
| id             | integer  | NO        | ID                                 |
| game_id        | integer  | NO        | 試合 ID                            |
| player_id      | integer  | NO        | プレイヤー ID                      |
| score          | integer  | NO        | 麻雀の持ち点を表すスコア           |
| points         | numeric  | NO        | 順位点を加味したポイント           |
| penalty_points | numeric  | NO        | チョンボなど減点を表す反則ポイント |
| rank           | integer  | NO        | 順位                               |

### kyoku_player_result（局単位のプレイヤーの結果）

**主キー**: id
**外部キー**: kyoku_id -> kyoku.id, player_id -> player.id

| カラム名    | データ型             | NULL 許可 | 説明          |
| ----------- | -------------------- | --------- | ------------- |
| id          | integer              | NO        | ID            |
| kyoku_id    | integer              | NO        | 局 ID         |
| player_id   | integer              | NO        | プレイヤー ID |
| score       | integer              | NO        | スコア        |
| player_wind | ENUM(1z, 2z, 3z, 4z) | NO        | 自風          |

### team_season_result（シーズン単位のチームの結果）

> [!Note]
> ビュー

**主キー**: id

| カラム名                 | データ型                        | NULL 許可 | 説明                                                                                                 |
| ------------------------ | ------------------------------- | --------- | ---------------------------------------------------------------------------------------------------- |
| team_id                  | integer                         | NO        | ID                                                                                                   |
| team_name                | varchar                         | NO        | チーム名                                                                                             |
| league_season_start_year | integer                         | NO        | シーズンの開始年度                                                                                   |
| league_season_end_year   | integer                         | NO        | シーズンの終了年度                                                                                   |
| season_stage_type        | ENUM(regular, semifinal, final) | NO        | シーズン種別                                                                                         |
| base_points              | numeric                         | NO        | チームごとの games テーブルの points の合計                                                          |
| final_points             | numeric                         | NO        | base_points に regular, semifinal からの持ち越しポイントを加算した値。この値を使用して優勝を決定する |

### team_base_points（シーズンにおける base points）

> [!WARNING]
> team_season_result を使用する。一時テールのため team_base_points は使わない。

## イベントテーブル

### event（イベント）

> [!Note]
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

| カラム名       | データ型         | NULL 許可 | 説明                       |
| -------------- | ---------------- | --------- | -------------------------- |
| event_id       | integer          | NO        | イベント ID                |
| type           | ENUM(omote, ura) | NO        | ドラ種別（表ドラ・裏ドラ） |
| dora_indicator | varchar          | NO        | ドラ表示牌                 |
| dora           | varchar          | NO        | ドラ牌                     |

#### haipai_event（配牌イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, player_id -> player.id

| カラム名       | データ型 | NULL 許可 | 説明                                                    |
| -------------- | -------- | --------- | ------------------------------------------------------- |
| event_id       | integer  | NO        | イベント ID                                             |
| player_id      | integer  | NO        | プレイヤー ID                                           |
| hand           | varchar  | NO        | 配牌時の手牌                                            |
| tenho_possible | boolean  | NO        | 配牌時に天鳳チャンスであるか（親でシャンテン数が 0 か） |
| chiho_possible | boolean  | NO        | 配牌時に地和チャンスであるか（子でシャンテン数が 0 か） |

#### agari_event（ツモあがり、ロンあがりイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id, target_player_id -> player.id

| カラム名         | データ型 | NULL 許可 | 説明                                                           |
| ---------------- | -------- | --------- | -------------------------------------------------------------- |
| event_id         | integer  | NO        | イベント ID                                                    |
| actor_player_id  | integer  | NO        | 和了したプレイヤー ID                                          |
| target_player_id | integer  | YES       | 放銃したプレイヤー ID（ツモあがりの場合は null）               |
| points           | integer  | NO        | リーチ棒や本場のポイントを含む和了時のポイント（加算ポイント） |
| base_points      | integer  | NO        | リーチ棒や本場のポイントは含まれない和了時のポイント           |
| winning_tile     | varchar  | NO        | ロン（放銃）牌                                                 |
| fu               | integer  | NO        | 合計の符                                                       |
| han              | integer  | NO        | 合計の翻数                                                     |
| is_called        | boolean  | NO        | 鳴いたあがりかどうか（false は面前のあがりを意味する）         |
| is_yakuman       | boolean  | NO        | 役満フラグ                                                     |
| description      | varchar  | NO        | 役と点数の説明                                                 |

##### yaku_event（あがり時の役）

**主キー**: event_id
**外部キー**: event_id -> event.id, name_id -> name.id

| カラム名 | データ型 | NULL 許可 | 説明                     |
| -------- | -------- | --------- | ------------------------ |
| event_id | integer  | NO        | イベント ID              |
| name_id  | integer  | NO        | 役の名前に対する外部キー |
| han      | integer  | NO        | 役の翻数                 |

#### ryuyoku_event（流局イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id

| カラム名 | データ型        | NULL 許可 | 説明        |
| -------- | --------------- | --------- | ----------- |
| event_id | integer         | NO        | イベント ID |
| reason   | ENUM(end_kyoku) | NO        | 流局理由    |

##### ryukyoku_player_event（流局時のプレイヤー情報）

**主キー**: id
**外部キー**: event_id -> event.id, player_id -> player.id

| カラム名  | データ型 | NULL 許可 | 説明                                   |
| --------- | -------- | --------- | -------------------------------------- |
| id        | integer  | NO        | ID                                     |
| event_id  | integer  | NO        | イベント ID                            |
| player_id | integer  | NO        | プレイヤー ID                          |
| is_tenpai | boolean  | NO        | 聴牌かどうか（false はノーテンを表す） |

#### reach_event（リーチイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名        | データ型 | NULL 許可 | 説明                                                                                             |
| --------------- | -------- | --------- | ------------------------------------------------------------------------------------------------ |
| event_id        | integer  | NO        | イベント ID                                                                                      |
| actor_player_id | integer  | NO        | リーチプレイヤー ID                                                                              |
| is_accepted     | boolean  | NO        | リーチ宣言が受け入れられたかのフラグ。false であればリーチ宣言で放銃した（ロンされた）と言える。 |

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

| カラム名        | データ型 | NULL 許可 | 説明                  |
| --------------- | -------- | --------- | --------------------- |
| event_id        | integer  | NO        | イベント ID           |
| actor_player_id | integer  | NO        | ツモしたプレイヤー ID |
| tile            | varchar  | NO        | ツモした牌            |
| is_rinshan      | boolean  | NO        | 嶺上フラグ            |

### 鳴き関連テーブル

#### chi_event（チーイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id, target_player_id -> player.id

| カラム名         | データ型 | NULL 許可 | 説明                    |
| ---------------- | -------- | --------- | ----------------------- |
| event_id         | integer  | NO        | イベント ID             |
| actor_player_id  | integer  | NO        | チーしたプレイヤー ID   |
| target_player_id | integer  | NO        | 牌を捨てたプレイヤー ID |
| tile             | varchar  | NO        | チーした牌              |
| block            | varchar  | NO        | 鳴いた後の牌のブロック  |

#### pon_event（ポンイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id, target_player_id -> player.id

| カラム名         | データ型 | NULL 許可 | 説明                    |
| ---------------- | -------- | --------- | ----------------------- |
| event_id         | integer  | NO        | イベント ID             |
| actor_player_id  | integer  | NO        | ポンしたプレイヤー ID   |
| target_player_id | integer  | NO        | 牌を捨てたプレイヤー ID |
| block            | varchar  | NO        | 鳴いた後の牌のブロック  |
| tile             | varchar  | NO        | ポンした牌              |

#### an_kan_event（暗槓イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名        | データ型 | NULL 許可 | 説明                   |
| --------------- | -------- | --------- | ---------------------- |
| event_id        | integer  | NO        | イベント ID            |
| actor_player_id | integer  | NO        | カンしたプレイヤー ID  |
| block           | varchar  | NO        | 鳴いた後の牌のブロック |

#### dai_kan_event（大明槓イベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名        | データ型 | NULL 許可 | 説明                   |
| --------------- | -------- | --------- | ---------------------- |
| event_id        | integer  | NO        | イベント ID            |
| actor_player_id | integer  | NO        | カンしたプレイヤー ID  |
| tile            | varchar  | NO        | カンをした牌           |
| block           | varchar  | NO        | 鳴いた後の牌のブロック |

#### sho_kan_event（小明槓・カカンイベント）

**主キー**: event_id
**外部キー**: event_id -> event.id, actor_player_id -> player.id

| カラム名        | データ型 | NULL 許可 | 説明                   |
| --------------- | -------- | --------- | ---------------------- |
| event_id        | integer  | NO        | イベント ID            |
| actor_player_id | integer  | NO        | カンしたプレイヤー ID  |
| tile            | varchar  | NO        | カンをした牌           |
| block           | varchar  | NO        | 鳴いた後の牌のブロック |

## その他のテーブル

### yaku_name（役定義のテーブル）

> [!NOTE]
> name_furigana を使用して役名をカタカナ名で検索できる。

**主キー**: id

| カラム名      | データ型 | NULL 許可 | 説明                 |
| ------------- | -------- | --------- | -------------------- |
| id            | integer  | NO        | ID                   |
| name          | varchar  | NO        | 役の名前             |
| name_furigana | varchar  | NO        | カタカナの役の名前牌 |

### player_state（ある巡目におけるプレイヤーの状態）

> [!NOTE]
> event_id よりどのイベント時の状態か確認できる。
> turn_number からある巡目の情報を確認できる。0 は配牌時の状態を表す。
> 特別な要件がなければシャンテン数には shanten_count を使用する。

**主キー**: event_id
**外部キー**: event_id -> event.id, player_id -> player.id

| カラム名                       | データ型 | NULL 許可 | 説明                                                                       |
| ------------------------------ | -------- | --------- | -------------------------------------------------------------------------- |
| event_id                       | integer  | NO        | イベント ID                                                                |
| player_id                      | integer  | NO        | プレイヤー ID                                                              |
| hand                           | varchar  | NO        | 手牌                                                                       |
| called_blocks                  | varchar  | NO        | 鳴いて晒した牌のブロック                                                   |
| shanten_count                  | integer  | NO        | シャンテン数（標準形、七対子、国士無双のシシャンテン数数の内最小の値）     |
| standard_type_shanten_count    | integer  | NO        | 標準形のシャンテン数                                                       |
| seven_pairs_shanten_count      | integer  | NO        | 七対子のシャンテン数                                                       |
| thirteen_orphans_shanten_count | integer  | NO        | 国士無双のシャンテン数                                                     |
| is_reached                     | boolean  | NO        | リーチ状態か                                                               |
| turn_number                    | integer  | NO        | 何巡目のプレイヤーの情報かを表す（プレイヤーの打牌回数）。0 は配牌時の情報 |

### foul_play（反則行為・チョンボ）

**主キー**: id
**外部キー**: kyoku_id -> kyoku.id, actor_player_id -> player.id

| カラム名        | データ型                                                   | NULL 許可 | 説明                                                |
| --------------- | ---------------------------------------------------------- | --------- | --------------------------------------------------- |
| id              | integer                                                    | NO        | ID                                                  |
| kyoku_id        | integer                                                    | NO        | 局 ID（外部キー）                                   |
| actor_player_id | integer                                                    | NO        | 反則・チョンボを行ったプレイヤー ID（外部キー）     |
| penalty_points  | numeric                                                    | NO        | 反則・チョンボのペナルティポイント（デフォルト: 0） |
| description     | varchar                                                    | NO        | 反則・チョンボの詳細説明                            |
| type            | ENUM(誤リーチ, 誤ポン, 語チー, 少牌, 多牌, 誤ツモ, 誤ロン) | NO        | 反則・チョンボの種類                                |
