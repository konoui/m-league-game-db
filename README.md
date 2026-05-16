## M リーグ試合情報データベース

M リーグの試合情報を保存した sqlite3 形式のデータベースを提供するリポジトリです。

## ダウンロード方法

[最新のリリース情報からダウンロードできます。](https://github.com/konoui/m-league-game-db/releases/latest)

ダウンロード例

```bash
curl -L -O https://github.com/konoui/m-league-game-db/releases/latest/download/database.zip
```

実行例

```bash
sqlite3 database.sqlite3 "SELECT * FROM player;"
```

## テーブル定義

[こちらを参照ください。](./TABLE.md)

## SQL クエリ例

[こちらを参照ください。](./query-examples/README.md)

## 麻雀牌の表し方

[こちらを参照ください。](./PAI_FORMAT.md)

## 役名一覧

[こちらを参照ください。](./YAKU_NAMES.md)

## 留意事項

- データの正確性には注意をしていますが、間違いなどあれば Issue より報告いただけると助かります。
  - リーチ宣言の数について、リーチ宣言時放銃した場合のカウントに問題がある可能性があります。
- 局、試合単位の点数や結果に誤りはないと考えられます。

## 要望など

- 機能要望リクエストなどあれば Issue を作成ください。

## データの利用について

- 利用許可の申請や利用の明記は不要です。自由にお使いください。
- 利用していただけている場合は、Issue やSNS などでひと言いただけると励みになります。
- M リーグをより楽しんだり盛り上げていただけると幸いです。

## 関連記事

- [Note M リーグの過去試合情報のデータベースを公開しました](https://note.com/konoui/n/nd4916f94485e)
- [Note M リーグの牌譜を天鳳形式で公開しました](https://note.com/konoui/n/n42bd1adb3f30)
  - [天鳳形式の M リーグ牌譜](https://m-league.konoui.dev/)
