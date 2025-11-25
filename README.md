## M リーグ試合情報データベース

M リーグの試合情報を保存した sqlite3 形式のデータベースを提供するリポジトリです。

## ダウンロード方法

[最新のリリース情報からダウンロードできます。](https://github.com/konoui/m-league-game-db/releases/latest)

実行例

```bash
sqlite3 database.sqlite3 "SELECT * FROM player;"
```

## テーブル定義

[こちらを参照してください。](./TABLE.md)

## SQL クエリ例

[こちらを参照してください。](./query-examples/README.md)

## 留意事項

- データの正確性には注意をしていますが、間違いなどあれば Issue より報告いただけると助かります。
  - リーチ宣言の数について、リーチ宣言時放銃した場合のカウントに問題がある可能性があります。
- 機能要望リクエストがあれば Issue を作成ください。
- 局、試合単位の点数や結果に誤りはないと考えられます。
