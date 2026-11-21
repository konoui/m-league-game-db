# M リーグ DB のローカル MCP サーバー

M リーグの試合データベース（DuckDB 版）に、Claude Code や Claude Desktop から自然言語で質問するための MCP サーバーです。

`.mcpb`（Claude Desktop 用）はビルド時に解決した `uv.lock` を同梱するため、利用者の環境でも同じバージョンの依存関係で動きます。

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
| `get_doc` | 用語集・ルール・牌の表記・役名などの文書 |
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
| `MLEAGUE_RELEASE_REPO` | 取得元のリポジトリ（既定 `konoui/m-league-game-db`）。DB はこのリポジトリの Latest リリースから、クエリ例は `main` から取る |
| `MLEAGUE_UPDATE_INTERVAL_S` | DB の更新を確かめる間隔（秒、既定 1 日） |
| `MLEAGUE_EXAMPLES_INTERVAL_S` | クエリ例の更新を確かめる間隔（秒、既定 7 日）。DB を取得・更新したときは間隔によらず確かめる |
| `MLEAGUE_UPDATE_EXAMPLES` | `0` でクエリ例の取得をやめ、同梱版だけを使う |

## 用語集

`GLOSSARY.md` は麻雀用語と DB の列の対応です。M リーグ固有のルール（数え役満なしなど）もここに書いています。`get_doc` で Claude が参照します。よく使う SQL の型は `queries/` の検証済みクエリ例にまとめてあり、`search_query_examples` から検索できます。

スキーマ文書（`TABLE.duckdb.md` など）は、DB の初回取得時にリリース zip からキャッシュディレクトリ（既定 `~/.cache/m-league-game-db/docs/`）に展開し、DB と同じ版を優先して読みます。キャッシュがないときは .mcpb に同梱した文書を使います。

クエリ例は .mcpb に同梱した版に加えて、取得元のリポジトリの `main` から新しい版を取得します（キャッシュは `~/.cache/m-league-game-db/queries/`）。

- `queries/` を最後に変えたコミットを GitHub API で確かめ、前回と違うときだけ、そのコミットの zip から `meta.json` と `query.sql` を取ります。
- 確かめるのは、DB を取得・更新したとき（スキーマが変わってクエリ例が合わなくなりうるとき）と、前回から 7 日たったときです。
- 取得したクエリ例のうち、手元の DB で `EXPLAIN` が通るものだけを使います。取得した SQL を実行しないよう、`EXPLAIN` にかけるのは SELECT 1 文だけのクエリに限り（複数文や `EXPLAIN ANALYZE` は外す）、1 件 5 秒で打ち切ります。通らないものは同梱版で代え、同梱版にもなければ外します。DB とクエリ例の版がずれても、存在しない列やテーブルを使う例を渡さないためです。
- 取得や検証に失敗したら、手元のキャッシュか同梱版をそのまま使います。
- `MLEAGUE_DB` や `MLEAGUE_DOC_ROOT` を指定しているとき、リポジトリ内で直接起動したときは取得せず、`queries/` をそのまま読みます。
- `main` に入れたクエリ例は、拡張機能を出し直さなくても利用者に届きます。外部からの PR を取り込むときは、その前提でレビューしてください。

## 詳しくない人向けの導入手順

`GUIDE.md` を参照してください。`./build_mcpb.sh` で Claude Desktop 用の拡張機能 `dist/m-league-db.mcpb` を作れます。

## 拡張機能のリリース

`mcpb-v<X.Y.Z>` のタグを push すると、`.github/workflows/release-mcpb.yml` が `.mcpb` をビルドして動作を確かめ、同じ名前のリリースに載せます。

```bash
git tag mcpb-v0.1.0
git push origin mcpb-v0.1.0
```

ダウンロード URL は版ごとに `https://github.com/konoui/m-league-game-db/releases/download/mcpb-v<X.Y.Z>/m-league-db.mcpb` です。常に最新版を指す固定の URL は用意しないので、利用者には版を指定して取得してもらいます。

- 拡張機能のリリースは Latest にしません。Latest のリリースは DB として、`server.py`・CI・`scripts/validate.py`・m-league-score-sheet の日々の DB 作成が取得するためです。Latest が拡張機能のリリースになると、日々の DB 作成が止まります。
- 拡張機能のリリースは、このワークフローからだけ作ります。画面から手で作ったり編集したりしないでください（「Set as the latest release」が付くことがあります）。
- `.mcpb` には、ビルド時点のクエリ例（`queries/`）と `MLEAGUE.md` を同梱します。クエリ例は利用者の手元で `main` から更新されますが、`MLEAGUE.md` を届けるには新しいタグでリリースし直します。
- `mcp-server/` を変更した PR では、ビルドと動作確認だけを行います。
