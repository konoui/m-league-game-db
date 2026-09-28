# M リーグ DB のローカル MCP サーバー

M リーグの試合データベース（DuckDB 版）に、Claude Code や Claude Desktop から自然言語で質問するための MCP サーバーです。

## 必要なもの

- [uv](https://docs.astral.sh/uv/)（依存関係は `server.py` の先頭に書いてあり、初回起動時に自動で入ります）

## 登録

Claude Code:

```bash
claude mcp add --scope user m-league-db -- uv run --script /path/to/m-league-game-db/mcp-server/server.py
```

Claude Desktop（`claude_desktop_config.json`）:

```json
{
  "mcpServers": {
    "m-league-db": {
      "command": "uv",
      "args": ["run", "--script", "/path/to/m-league-game-db/mcp-server/server.py"]
    }
  }
}
```

初回起動時に GitHub Releases から最新の `duckdb.zip`（約 22MB）を取得し、`~/.cache/m-league-game-db/` に置きます。

## HTTP で起動する（ChatGPT などリモート接続用）

```bash
uv run --script server.py --http --port 8765 --allowed-host <トンネルのホスト名>
```

`127.0.0.1:8765/mcp` で Streamable HTTP を待ち受けます。外部からはトンネル（cloudflared や ngrok）経由で接続し、そのホスト名を `--allowed-host` に渡します。指定していないホスト名での接続は拒否します。認証はないので、公開 URL は使うときだけ立ち上げてください。

## ツール

| ツール | 内容 |
| --- | --- |
| `run_sql` | 読み取り専用で SQL を実行する（30 秒でタイムアウト、最大 1000 行） |
| `list_tables` | テーブル一覧と日本語の説明 |
| `describe_table` | 列の型と、TABLE.duckdb.md の説明・注意書き |
| `search_query_examples` | `queries/` の検証済みクエリ例から似たものを探す |
| `find_player` | 選手を名前・ふりがなで探し、所属チームの履歴を返す |
| `get_doc` | よく使う SQL の型・用語集・ルール・牌の表記・役名などの文書 |
| `database_info` | DB のリリースタグとデータの期間 |
| `update_database` | 最新のリリースに差し替える |

## 安全性

- DB は読み取り専用で開き、外部ファイルへのアクセス（`read_csv`、`ATTACH` など）を禁止しています。
- 参照系以外の SQL は実行前に拒否します。

## 環境変数

| 変数 | 内容 |
| --- | --- |
| `MLEAGUE_DB` | 手元の `.duckdb` を使う（自動取得しない） |
| `MLEAGUE_CACHE_DIR` | キャッシュの場所（既定 `~/.cache/m-league-game-db`） |
| `MLEAGUE_RELEASE_REPO` | 取得元のリポジトリ（既定 `konoui/m-league-game-db`） |

## 用語集と SQL の型

`GLOSSARY.md` は麻雀用語と DB の列の対応です。M リーグ固有のルール（数え役満なしなど）もここに書いています。`RECIPES.md` は連続記録や率のランキングなど、よく使う SQL の型です。どちらも `get_doc` で Claude が参照します。

## 詳しくない人向けの導入手順

`GUIDE.md` を参照してください。`./build_mcpb.sh` で Claude Desktop 用の拡張機能 `dist/m-league-db.mcpb` を作れます。
