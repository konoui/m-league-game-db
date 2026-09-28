# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2,<3", "duckdb>=1.1", "httpx>=0.27"]
# ///
"""M リーグ試合データベースのローカル MCP サーバー（教えてMリーグハカセ用）。

- DB は GitHub Releases の DuckDB 版を初回に取得してキャッシュする
  （既定: ~/.cache/m-league-game-db/。環境変数 MLEAGUE_DB で任意の .duckdb を指定可）
- SQL は読み取り専用・外部ファイルアクセス禁止・タイムアウト・行数上限つきで実行する
- スキーマ文書・用語集・クエリ例（queries/）をツールとして引ける

起動: uv run --script mcp-server/server.py   （stdio）
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import threading
import zipfile
from pathlib import Path

import duckdb
import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

logging.getLogger("httpx").setLevel(logging.WARNING)

HERE = Path(__file__).resolve().parent
# 拡張機能（.mcpb）では server.py の隣の docs/ に文書とクエリ例を同梱する。リポジトリ内ではリポジトリ直下を読む
REPO = Path(os.environ["MLEAGUE_DOC_ROOT"]) if os.environ.get("MLEAGUE_DOC_ROOT") else (HERE / "docs" if (HERE / "docs").is_dir() else HERE.parent)
RELEASE_REPO = os.environ.get("MLEAGUE_RELEASE_REPO", "konoui/m-league-game-db")
CACHE_DIR = Path(os.environ.get("MLEAGUE_CACHE_DIR", Path.home() / ".cache" / "m-league-game-db"))
DB_PATH = Path(os.environ["MLEAGUE_DB"]) if os.environ.get("MLEAGUE_DB") else CACHE_DIR / "database.duckdb"
TAG_PATH = CACHE_DIR / "release_tag.txt"

CHECKED_PATH = CACHE_DIR / "last_checked.txt"
UPDATE_INTERVAL_S = int(os.environ.get("MLEAGUE_UPDATE_INTERVAL_S", 24 * 3600))
_update_lock = threading.Lock()

SQL_TIMEOUT_S = 30
DEFAULT_ROWS = 100
MAX_ROWS = 1000

mcp = MCPServer(
    "m-league-db",
    instructions=(
        "M リーグ（プロ麻雀リーグ）の全試合データ（2018-19 シーズン以降の試合・局・打牌単位）を DuckDB で引けるサーバー。\n"
        "進め方: 1) 質問の解釈を決める（期間、ステージ、集計単位、連続記録をシーズンで区切るか、率を比べるときの試合数の下限）。"
        "2) search_query_examples で似たクエリ例を探し、よく使う型は get_doc('recipes') を見る。"
        "3) 麻雀用語は get_doc('glossary') で列との対応を確かめ、選手名は find_player で正式表記にする。列は describe_table で確かめる。"
        "4) run_sql で実行する。5) 1 位の記録などは、該当期間の試合を 1 行ずつ並べて集計と一致するか確かめる。\n"
        "答え方: 結論を先に書き、表で示し、最後に数え方（解釈・試合数の下限・区切り方）とデータの最終試合日（database_info）を書く。\n"
        "注意: M リーグは数え役満なし（役満は agari_event.is_yakuman で判定）。試合時点のチームは game_player_result.team_id。"
        "クエリ例の player_team の年度範囲での結合やシーズン区切りの連続記録は古い書き方なので、方針に合わせて直す。"
        "トップ率などの定型指標は集計ビュー player_season_stage_stats にある。"
        "2025-26 シーズン以降は同じ時間帯に 2 卓あるので、試合は game_id で特定する。"
        "ツールが使えないときは推測で数字を答えない。"
    ),
)


# ---------------------------------------------------------------- DB
def _download_latest() -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=120) as c:
        rel = c.get(f"https://api.github.com/repos/{RELEASE_REPO}/releases/latest").json()
        tag = rel.get("tag_name", "unknown")
        url = next(a["browser_download_url"] for a in rel["assets"] if a["name"] == "duckdb.zip")
        data = c.get(url).content
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        name = next(n for n in z.namelist() if n.endswith(".duckdb"))
        tmp = CACHE_DIR / "database.duckdb.tmp"
        tmp.write_bytes(z.read(name))
    tmp.replace(CACHE_DIR / "database.duckdb")  # atomic swap
    TAG_PATH.write_text(tag)
    return tag


def _latest_tag() -> str:
    with httpx.Client(follow_redirects=True, timeout=15) as c:
        return c.get(f"https://api.github.com/repos/{RELEASE_REPO}/releases/latest").json()["tag_name"]


def _maybe_update() -> None:
    """前回の確認から UPDATE_INTERVAL_S 以上たっていれば、新しいリリースがあるか確かめて差し替える。
    オフラインや GitHub の制限で失敗しても、手元の DB でそのまま動く。"""
    import time
    try:
        last = float(CHECKED_PATH.read_text()) if CHECKED_PATH.exists() else 0.0
    except ValueError:
        last = 0.0
    if time.time() - last < UPDATE_INTERVAL_S:
        return
    with _update_lock:
        try:
            current = TAG_PATH.read_text().strip() if TAG_PATH.exists() else None
            if _latest_tag() != current:
                _download_latest()
        except Exception as e:  # noqa: BLE001 - 更新の失敗で質問への回答を止めない
            logging.getLogger(__name__).warning("DB の更新確認に失敗しました（手元の DB を使います）: %s", e)
        finally:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            CHECKED_PATH.write_text(str(time.time()))


def _ensure_db() -> Path:
    if not DB_PATH.exists():
        if os.environ.get("MLEAGUE_DB"):
            raise FileNotFoundError(f"MLEAGUE_DB={DB_PATH} が見つかりません")
        _download_latest()
        CHECKED_PATH.write_text(str(__import__("time").time()))
    elif not os.environ.get("MLEAGUE_DB"):
        _maybe_update()
    return DB_PATH


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(_ensure_db()), read_only=True, config={"enable_external_access": False})
    con.execute("SET lock_configuration = true")
    return con


def _query(sql: str, max_rows: int) -> dict:
    con = _connect()
    timer = threading.Timer(SQL_TIMEOUT_S, con.interrupt)
    timer.start()
    try:
        rel = con.sql(sql)
        if rel is None:
            return {"error": "結果を返す SELECT 文を渡してください"}
        cols = rel.columns
        rows = rel.fetchmany(max_rows + 1)
        truncated = len(rows) > max_rows
        rows = rows[:max_rows]
        return {"columns": cols, "rows": [[_jsonable(v) for v in r] for r in rows], "row_count": len(rows), "truncated": truncated}
    except duckdb.InterruptException:
        return {"error": f"{SQL_TIMEOUT_S} 秒でタイムアウトしました。条件を絞るか集計を単純にしてください"}
    except duckdb.Error as e:
        return {"error": str(e)[:1500]}
    finally:
        timer.cancel()
        con.close()


def _jsonable(v):
    if isinstance(v, float):
        return round(v, 6)  # FLOAT 列の 11.199999809 のような誤差を消す
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return str(v)


_READONLY = re.compile(r"^\s*(--[^\n]*\n\s*|/\*.*?\*/\s*)*(select|with|from|describe|show|summarize|pivot|unpivot|explain)\b", re.I | re.S)


# ---------------------------------------------------------------- docs & examples
def _read(name: str) -> str:
    return (REPO / name).read_text(encoding="utf-8")


def _table_sections() -> dict[str, str]:
    md = _read("TABLE.duckdb.md")
    out = {}
    for m in re.finditer(r"^#{3,4} ([a-z_]+)（(.+?)）\n(.*?)(?=^#{2,4} |\Z)", md, re.M | re.S):
        out[m.group(1)] = f"### {m.group(1)}（{m.group(2)}）\n{m.group(3).strip()}"
    return out


def _examples() -> list[dict]:
    items = []
    for d in sorted((REPO / "queries").iterdir()):
        if not (d / "meta.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        items.append({"name": d.name, "description": meta["description"], "plan": meta.get("plan", []),
                      "tables": meta.get("tables", []), "sql": (d / "query.sql").read_text(encoding="utf-8").strip()})
    return items


SYNONYMS = {
    "トップ": "1着", "ラス": "4着", "ラス回避": "4着回避", "連帯": "連対", "振り込み": "放銃", "振込": "放銃",
    "和了": "あがり", "上がり": "あがり", "アガリ": "あがり", "テンパイ": "聴牌", "ノーテン": "不聴", "立直": "リーチ",
    "鳴き": "仕掛け", "副露": "仕掛け", "チーム成績": "チーム別", "選手": "プレイヤー", "個人": "プレイヤー",
}


def _normalize(s: str) -> str:
    for k, v in SYNONYMS.items():
        s = s.replace(k, v)
    return s


def _bigrams(s: str) -> set[str]:
    s = re.sub(r"\s+", "", s.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


DOCS = {
    "recipes": ((REPO / "RECIPES.md") if (REPO / "RECIPES.md").exists() else (HERE / "RECIPES.md"), "よく使う SQL の型（連続記録・率ランキング・直接対決・役満一覧・生の行での確認）"),
    "glossary": ((REPO / "GLOSSARY.md") if (REPO / "GLOSSARY.md").exists() else (HERE / "GLOSSARY.md"), "麻雀・M リーグ用語と DB の列の対応"),
    "mleague": (REPO / "MLEAGUE.md", "M リーグのルール（シーズン構成・得点計算）"),
    "tables": (REPO / "TABLE.duckdb.md", "全テーブルの詳細な説明（長い）"),
    "naming": (REPO / "DB_NAMING.md", "DB の命名規則"),
    "pai_format": (REPO / "PAI_FORMAT.md", "牌の表記"),
    "yaku_names": (REPO / "YAKU_NAMES.md", "役名一覧"),
    "changelog": (REPO / "DB_CHANGELOG.md", "DB の変更履歴"),
}


# ---------------------------------------------------------------- tools
@mcp.tool()
def run_sql(sql: str, max_rows: int = DEFAULT_ROWS) -> dict:
    """M リーグ DB（DuckDB）に読み取り専用の SQL を実行する。

    SELECT / WITH / DESCRIBE / SUMMARIZE などの参照系のみ。外部ファイルの読み込みは禁止、30 秒でタイムアウト。
    max_rows は 1〜1000（既定 100）。結果は {columns, rows, row_count, truncated} か {error}。
    """
    if not _READONLY.match(sql):
        raise ToolError("参照系の SQL（SELECT / WITH / DESCRIBE など）だけが実行できます")
    res = _query(sql, max(1, min(int(max_rows), MAX_ROWS)))
    if "error" in res:
        raise ToolError(res["error"])
    return res


@mcp.tool()
def list_tables() -> list[dict]:
    """テーブルとビューの一覧を、日本語の説明と行数つきで返す。"""
    sections = _table_sections()
    res = _query("SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name", 500)
    out = []
    for name, ttype in res.get("rows", []):
        title = re.search(r"（(.+?)）", sections.get(name, "")) if name in sections else None
        out.append({"name": name, "type": "view" if ttype == "VIEW" else "table", "description": title.group(1) if title else ""})
    return out


@mcp.tool()
def describe_table(table: str) -> dict:
    """テーブルの列（型）と、TABLE.duckdb.md にある説明・注意書きを返す。"""
    if not re.fullmatch(r"[a-z_]+", table):
        raise ToolError("テーブル名が不正です")
    cols = _query(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position", 500)
    if not cols.get("rows"):
        raise ToolError(f"テーブル {table} はありません。list_tables で確認してください")
    return {"table": table, "columns": [dict(zip(["name", "type", "nullable"], r)) for r in cols["rows"]],
            "doc": _table_sections().get(table, "")}


@mcp.tool()
def search_query_examples(query: str, limit: int = 3, include_sql: bool = True) -> list[dict]:
    """queries/ にある検証済みのクエリ例から、質問に近いものを探す。

    似た集計（連続記録、リーチ率、シャンテン数など）の書き方・定義を確認するのに使う。
    """
    q = _bigrams(_normalize(query))
    scored = []
    for ex in _examples():
        text = ex["description"] + " " + " ".join(ex["plan"])
        b = _bigrams(_normalize(text))
        score = len(q & b) / (len(q) or 1)
        scored.append((score, ex))
    scored.sort(key=lambda x: -x[0])
    out = []
    for score, ex in scored[: max(1, min(limit, 10))]:
        item = {"name": ex["name"], "description": ex["description"], "plan": ex["plan"], "tables": ex["tables"], "score": round(score, 3)}
        if include_sql:
            item["sql"] = ex["sql"]
        out.append(item)
    return out


@mcp.tool()
def find_player(name: str) -> list[dict]:
    """選手を名前・ふりがなの部分一致で探し、所属チームの履歴も返す。表記ゆれや読みからの検索に使う。"""
    like = "%" + name.replace("'", "''").replace(" ", "").replace("　", "") + "%"
    res = _query(f"""
        SELECT p.id, p.name, p.name_furigana, p.joined_season_year,
               list(t.name || ' (' || pt.joined_season_year || '-' || CASE WHEN pt.left_season_year IS NULL OR pt.left_season_year >= 9999 THEN '現在' ELSE CAST(pt.left_season_year AS VARCHAR) END || ')' ORDER BY pt.joined_season_year) AS teams
        FROM player p
        LEFT JOIN player_team pt ON pt.player_id = p.id
        LEFT JOIN team t ON t.id = pt.team_id
        WHERE replace(p.name, ' ', '') LIKE '{like}' OR p.name_furigana LIKE '{like}'
        GROUP BY ALL ORDER BY p.id""", 50)
    if "error" in res:
        raise ToolError(res["error"])
    return [dict(zip(["id", "name", "furigana", "joined_season_year", "teams"], r)) for r in res["rows"]]


@mcp.tool()
def get_doc(name: str) -> str:
    """参考文書を返す。name: recipes（よく使う SQL の型）, glossary（用語と列の対応）, mleague（ルール）, tables（全テーブル説明・長い）,
    naming, pai_format（牌の表記）, yaku_names（役名）, changelog。"""
    if name not in DOCS:
        return "name は次のいずれか: " + ", ".join(f"{k}（{v[1]}）" for k, v in DOCS.items())
    return DOCS[name][0].read_text(encoding="utf-8")


@mcp.tool()
def database_info() -> dict:
    """使っている DB ファイル・リリースのタグ・データの期間（最新の試合日）を返す。"""
    path = _ensure_db()
    res = _query("SELECT min(date), max(date), count(*) FROM game", 1)
    lo, hi, n = res["rows"][0] if res.get("rows") else (None, None, None)
    return {"db_path": str(path), "release_tag": TAG_PATH.read_text().strip() if TAG_PATH.exists() else "unknown",
            "first_game": lo, "latest_game": hi, "games": n, "size_mb": round(path.stat().st_size / 1e6, 1)}


@mcp.tool()
def update_database() -> dict:
    """GitHub Releases から最新の DuckDB 版を取得して差し替える（毎日更新される）。MLEAGUE_DB 指定時は使えない。"""
    if os.environ.get("MLEAGUE_DB"):
        return {"error": "MLEAGUE_DB で DB を指定しているため更新しません"}
    before = TAG_PATH.read_text().strip() if TAG_PATH.exists() else None
    tag = _download_latest()
    return {"previous_tag": before, "current_tag": tag, "updated": before != tag}


# ---------------------------------------------------------------- resources
@mcp.resource("mleague://docs/{name}")
def doc_resource(name: str) -> str:
    """参考文書（get_doc と同じ内容）。"""
    return get_doc(name)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="M リーグ DB の MCP サーバー")
    ap.add_argument("--http", action="store_true", help="stdio ではなく Streamable HTTP で待ち受ける（ChatGPT などリモート接続用）")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--allowed-host", action="append", default=[],
                    help="受け付ける Host ヘッダー（トンネルのホスト名など）。複数指定可")
    a = ap.parse_args()
    if not a.http:
        mcp.run(transport="stdio")
        return
    from mcp.server.transport_security import TransportSecuritySettings

    hosts = ["127.0.0.1", f"127.0.0.1:{a.port}", "localhost", f"localhost:{a.port}", *a.allowed_host]
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",  # 外部公開はトンネル経由のみ
        port=a.port,
        streamable_http_path="/mcp",
        stateless_http=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts),
    )


if __name__ == "__main__":
    main()
