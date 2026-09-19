## Claude Code で新しいクエリを作成する

[Claude Code](https://claude.com/claude-code) の skill を使って、クエリ例を作成できます。

1. `database.sqlite3` をリポジトリ直下に置く（上記のダウンロード方法を参照）
2. リポジトリ直下で `claude` を起動し、作りたいクエリを伝える

```text
/create-query シーズン別のプレイヤー別平均和了打点を算出するクエリを作ってください
/create-query Issue #30 のクエリを作ってください
```

計画を提示して承認を得てから、`queries/<説明>/` に `query.sql` と `meta.json` を作成し、検証と `query-examples/` の生成までを行います。既存クエリの見直しは `/review-query` で行えます。

検証は LLM を使わないスクリプトで、手動でも実行できます（[詳細](./scripts/README.md)）。

```bash
uv run scripts/validate.py   # 形式・SQL の実行・結果の不変条件を検証
uv run scripts/render.py     # queries/ から query-examples/ を生成
```
