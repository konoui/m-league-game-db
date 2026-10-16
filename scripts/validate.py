#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jsonschema>=4", "duckdb>=1.5.5"]
# ///
"""queries/<description>/ のクエリ例を検証する。

usage:
  uv run scripts/validate.py check [--fix] [--strict] [QUERY_DIR_OR_FILE ...]
  uv run scripts/validate.py update-result [--release TAG] [QUERY_DIR_OR_FILE ...]

check は次の順に検査する。DB が手元にない段階は飛ばして、その旨を表示する（--strict では失敗にする）。

- 形式: meta.json、description、plan、query.sql の書き方
- SQLite（database.sqlite3）: 実行できるか、tables が実際の参照と合うか、結果が checks を満たすか
- DuckDB（database.duckdb）: DuckDB 版でも実行できるか
- result.json: そこに書かれた版の DB での実行結果と一致するか

update-result は result.json を作り直す。すでにあるクエリはその版のまま、ないクエリは最新のリリースで作る。
--release TAG（latest で最新）を付けると、その版に進めて作り直す。

result.json は、クエリを書き換えたときに結果が変わったかどうかを差分として見えるようにするためのもの。
DB は日々更新されるので、result.json の db に書いたリリース（DuckDB 版）で結果を固定する。
そのリリースの DB は初回に gh でダウンロードし、.cache/snapshot-db/<タグ>/ に置く。
"""

import argparse
import datetime
import decimal
import difflib
import json
import re
import sqlite3
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import duckdb
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
QUERIES_DIR = ROOT / "queries"
SCHEMA_FILE = ROOT / "schema" / "meta.schema.json"
SQLITE_DB = ROOT / "database.sqlite3"
DUCKDB_DB = ROOT / "database.duckdb"
QUERY_FILES = {"query.sql", "meta.json"}
RESULT_FILE = "result.json"
OPTIONAL_FILES = {"PLAN.md", RESULT_FILE}
# result.json の版の DB を置く場所と、リリースのファイル名
CACHE_DIR = ROOT / ".cache" / "snapshot-db"
RELEASE_ASSET = "duckdb.zip"
# 1 クエリの実行時間上限（秒）
TIMEOUT = 120
# result.json との差分を表示する行数の上限
DIFF_LINES = 30

DESCRIPTION_RE = re.compile(
    r"^(?P<unit>シーズン・ステージ別の|シーズン別の|ステージ別の|暦年別の|全期間の)"
    r"(?P<target>プレイヤー別|チーム別|試合別|席別)"
    r".+"
    r"(?P<action>を算出する|を取得する|を分析する)クエリ$"
)
DESCRIPTION_MAX_LEN = 80
FORBIDDEN_CHARS = set('/\\:*?"<>|')

# plan に書かない SQL 用語（大文字小文字は区別しない）
SQL_WORDS = {
    "select", "from", "where", "join", "group", "order", "having", "union",
    "with", "cte", "materialized", "count", "sum", "avg", "min", "max",
    "case", "partition", "over", "row_number", "lag", "lead", "limit", "sql",
}
SNAKE_CASE_RE = re.compile(r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b")
CTE_START_RE = re.compile(r"^\s*(WITH\s+(RECURSIVE\s+)?)?\w+\s+AS\s*(MATERIALIZED\s*)?\(\s*$", re.I)

# 読み取り以外の操作は拒否する
ALLOWED_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}


class Result:
    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)


class Unavailable(Exception):
    """検査に必要な DB を用意できなかった。"""


# ---------------------------------------------------------------- 形式
def check_files(r: Result, d: Path) -> bool:
    names = {p.name for p in d.iterdir()}
    for missing in sorted(QUERY_FILES - names):
        r.error(f"{missing} がありません")
    for extra in sorted(names - QUERY_FILES - OPTIONAL_FILES):
        r.error(f"想定外のファイルです: {extra}（query.sql, meta.json, PLAN.md, result.json のみ置けます）")
    return QUERY_FILES <= names


def check_meta(r: Result, d: Path, meta: dict, schema_validator: Draft202012Validator):
    for e in schema_validator.iter_errors(meta):
        loc = "/".join(str(p) for p in e.absolute_path) or "(root)"
        r.error(f"meta.json スキーマ違反 [{loc}]: {e.message}")
    desc = meta.get("description")
    if not isinstance(desc, str):
        return

    if desc != d.name:
        r.error(f"ディレクトリ名と description が一致しません: dir={d.name!r} description={desc!r}")
    if not DESCRIPTION_RE.match(desc):
        r.error(
            "description が形式 [分析単位][対象別][記録・統計内容][範囲・条件][処理内容]クエリ に合いません"
            "（分析単位: シーズン・ステージ別の/シーズン別の/ステージ別の/暦年別の/全期間の、"
            "対象: プレイヤー別/チーム別/試合別/席別、処理内容: を算出する/を取得する/を分析するクエリ）"
        )
    if len(desc) > DESCRIPTION_MAX_LEN:
        r.error(f"description が {DESCRIPTION_MAX_LEN} 文字を超えています（{len(desc)} 文字）")
    if bad := sorted(set(desc) & FORBIDDEN_CHARS):
        r.error(f"description にファイル名禁止文字があります: {''.join(bad)}")
    if re.search(r"[A-Za-z]", desc):
        r.error("description に英字は使えません")
    if re.search(r"[0-9０-９]位", desc):
        r.error("description の順位は「○着」と表記します（例: 1位 → 1着）")
    if "配牌時" in desc and "0順目（配牌時）" not in desc:
        r.error("配牌時は「0順目（配牌時）」と表記します")

    for i, item in enumerate(meta.get("plan") or []):
        if not isinstance(item, str):
            continue
        if re.match(r"^\s*([-•*・]|\d+\.)\s*", item):
            r.error(f"plan[{i}] の先頭に箇条書き記号は不要です")
        found = set(SNAKE_CASE_RE.findall(item))
        found |= {w for w in re.findall(r"[A-Za-z_]+", item) if w.lower() in SQL_WORDS}
        if found:
            r.error(f"plan[{i}] に SQL 構文・識別子らしき語があります（自然言語で書く）: {', '.join(sorted(found))}")


def check_sql_style(r: Result, sql: str):
    if not sql.rstrip().endswith(";"):
        r.error("query.sql の末尾に ; がありません")
    if "/*" in sql:
        r.error("ブロックコメント /* */ は使えません（-- を使う）")
    if not re.search(r"^\s*-- ", sql, re.M):
        r.error("query.sql にコメント（-- ）がありません")
    lines = sql.splitlines()
    for i, line in enumerate(lines):
        if CTE_START_RE.match(line):
            prev = next((l for l in reversed(lines[:i]) if l.strip()), "")
            if not prev.strip().startswith("--"):
                r.error(f"query.sql {i + 1} 行目: CTE の直前に目的を説明する -- コメントがありません: {line.strip()}")


# ---------------------------------------------------------------- SQLite
def run_sql(r: Result, sql: str, known_tables: set[str]) -> tuple[set[str], list[str], list[tuple]] | None:
    conn = sqlite3.connect(f"file:{SQLITE_DB}?mode=ro", uri=True)
    read_tables: set[str] = set()
    denied: list[str] = []

    def authorizer(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ and arg1 in known_tables:
            read_tables.add(arg1)
        if action not in ALLOWED_ACTIONS:
            denied.append(str(action))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    deadline = time.monotonic() + TIMEOUT
    conn.set_authorizer(authorizer)
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10000)
    start = time.monotonic()
    try:
        cur = conn.execute(sql)  # 複数文は ProgrammingError になる
        rows = cur.fetchall()
        columns = [c[0] for c in cur.description]
    except (sqlite3.Error, sqlite3.Warning) as e:
        if denied:
            r.error(f"読み取り以外の操作は禁止です（SQLite action code: {', '.join(denied)}）")
        elif time.monotonic() > deadline:
            r.error(f"実行が {TIMEOUT} 秒を超えました")
        else:
            r.error(f"SQL 実行エラー: {e}")
        return None
    finally:
        conn.close()
    elapsed = time.monotonic() - start
    if not rows:
        r.error("結果が 0 行です")
    r.notes.append(f"{len(rows)} rows, {elapsed:.2f}s")
    return read_tables, columns, rows


def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def check_result(r: Result, checks: dict, columns: list[str], rows: list[tuple]):
    """meta.json の checks（結果の不変条件）を検査する。結果をメモリ上の SQLite に読み込んで評価する。"""
    if dup := sorted({c for c in columns if columns.count(c) > 1}):
        r.error(f"出力カラム名が重複しています: {', '.join(dup)}")
        return

    row_limits = checks.get("rows", {})
    if "min" in row_limits and len(rows) < row_limits["min"]:
        r.error(f"結果の行数 {len(rows)} が checks.rows.min={row_limits['min']} を下回ります")
    if "max" in row_limits and len(rows) > row_limits["max"]:
        r.error(f"結果の行数 {len(rows)} が checks.rows.max={row_limits['max']} を超えます")

    mem = sqlite3.connect(":memory:")
    # "存在しないカラム" が文字列リテラルとして扱われ、ルールが素通りするのを防ぐ
    mem.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DML, False)
    mem.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DDL, False)
    mem.execute(f"CREATE TABLE result ({', '.join(map(quote, columns))})")
    mem.executemany(f"INSERT INTO result VALUES ({', '.join('?' * len(columns))})", rows)

    unique = checks.get("unique", [])
    if missing := [c for c in unique if c not in columns]:
        r.error(f"checks.unique のカラムが結果にありません: {', '.join(missing)}（出力カラム: {', '.join(columns)}）")
    elif unique:
        keys = ", ".join(map(quote, unique))
        dups = mem.execute(f"SELECT {keys}, COUNT(*) FROM result GROUP BY {keys} HAVING COUNT(*) > 1").fetchall()
        if dups:
            r.error(f"checks.unique ({', '.join(unique)}) が重複する行が {len(dups)} 組あります。例: {dups[0][:-1]} が {dups[0][-1]} 行")

    for i, rule in enumerate(checks.get("rules", [])):
        if ";" in rule:
            r.error(f"checks.rules[{i}] に ; は使えません: {rule}")
            continue
        try:
            (count,) = mem.execute(f"SELECT COUNT(*) FROM result WHERE NOT ({rule})").fetchone()
            example = mem.execute(f"SELECT * FROM result WHERE NOT ({rule}) LIMIT 1").fetchone()
        except sqlite3.Error as e:
            r.error(f"checks.rules[{i}] を評価できません（{e}）: {rule}")
            continue
        if count:
            sample = ", ".join(f"{c}={v!r}" for c, v in zip(columns, example))
            r.error(f"checks.rules[{i}] に違反する行が {count} 行あります: {rule}\n    例: {sample}")
    mem.close()


def check_tables(r: Result, meta_path: Path, meta: dict, read_tables: set[str], fix: bool):
    declared = meta.get("tables") or []
    missing = sorted(read_tables - set(declared))
    extra = [t for t in declared if t not in read_tables]
    if not missing and not extra:
        return
    if fix:
        meta["tables"] = [t for t in declared if t in read_tables] + missing
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        r.notes.append(f"tables を修正しました（追加: {missing or 'なし'}, 削除: {extra or 'なし'}）")
        return
    if missing:
        r.error(f"tables に不足があります（SQL が参照）: {', '.join(missing)}（--fix で自動修正）")
    if extra:
        r.error(f"tables に SQL が参照しないテーブルがあります: {', '.join(extra)}（--fix で自動修正）")


# ---------------------------------------------------------------- DuckDB
def check_duckdb(r: Result, conn: duckdb.DuckDBPyConnection, sql: str):
    """DuckDB 版でも実行できるかを見る。どちらの配布物を使っても同じクエリ例が読めるようにするため。"""
    try:
        conn.execute(sql).fetchall()
    except duckdb.Error as e:
        r.error(f"DuckDB 実行エラー: {str(e).splitlines()[0]}")


# ---------------------------------------------------------------- result.json
def gh(*args: str) -> str:
    try:
        return subprocess.run(["gh", *args], capture_output=True, text=True, cwd=ROOT, check=True).stdout
    except FileNotFoundError:
        raise Unavailable("gh コマンドがありません") from None
    except subprocess.CalledProcessError as e:
        raise Unavailable(f"gh {' '.join(args)} に失敗しました: {e.stderr.strip()}") from None


def latest_release() -> str:
    return gh("release", "view", "--json", "tagName", "--jq", ".tagName").strip()


class ReleaseDatabases:
    """リリースのタグごとの DuckDB 版 DB。手元になければダウンロードする。"""

    def __init__(self):
        self.conns: dict[str, duckdb.DuckDBPyConnection] = {}
        self.unavailable: dict[str, str] = {}

    def connect(self, tag: str) -> duckdb.DuckDBPyConnection:
        if tag in self.unavailable:
            raise Unavailable(self.unavailable[tag])
        if tag not in self.conns:
            try:
                self.conns[tag] = duckdb.connect(str(self.download(tag)), read_only=True)
            except Unavailable as e:
                self.unavailable[tag] = str(e)
                raise
        return self.conns[tag]

    @staticmethod
    def download(tag: str) -> Path:
        d = CACHE_DIR / tag
        db = d / "database.duckdb"
        if db.exists():
            return db
        d.mkdir(parents=True, exist_ok=True)
        print(f"リリース {tag} の {RELEASE_ASSET} をダウンロードします", file=sys.stderr)
        gh("release", "download", tag, "--pattern", RELEASE_ASSET, "--dir", str(d), "--clobber")
        with zipfile.ZipFile(d / RELEASE_ASSET) as z:
            name = next(n for n in z.namelist() if n.endswith(".duckdb"))
            tmp = d / "database.duckdb.tmp"
            tmp.write_bytes(z.read(name))
        tmp.replace(db)
        (d / RELEASE_ASSET).unlink()
        return db


def cell(v):
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, (float, decimal.Decimal)):
        # 集計の順序による末尾の誤差を落とす
        return round(float(v), 6)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return str(v)


def render_result(conn: duckdb.DuckDBPyConnection, sql: str, tag: str) -> str:
    """実行結果を result.json の文字列にする。差分が読めるよう、結果の 1 行を 1 行に書く。"""
    cur = conn.execute(sql)
    columns = [c[0] for c in cur.description]
    rows = [json.dumps([cell(v) for v in row], ensure_ascii=False) for row in cur.fetchall()]
    lines = [
        "{",
        f'  "db": {json.dumps(tag)},',
        f'  "columns": {json.dumps(columns, ensure_ascii=False)},',
        '  "rows": [' + ("" if rows else "]"),
        *[f"    {r}{',' if i < len(rows) - 1 else ''}" for i, r in enumerate(rows)],
        *(["  ]"] if rows else []),
        "}",
    ]
    return "\n".join(lines) + "\n"


def recorded_release(result_path: Path) -> str | None:
    try:
        db = json.loads(result_path.read_text(encoding="utf-8")).get("db")
    except (json.JSONDecodeError, AttributeError):
        return None
    return db if isinstance(db, str) and db else None


def check_snapshot(r: Result, d: Path, sql: str, releases: ReleaseDatabases, strict: bool):
    result_path = d / RESULT_FILE
    if not result_path.exists():
        # 作成途中のクエリを止めないよう、--strict（CI）でだけ失敗にする
        if strict:
            r.error("result.json がありません（update-result で作成）")
        else:
            r.notes.append("result.json 未作成")
        return
    tag = recorded_release(result_path)
    if not tag:
        r.error("result.json の db が読めません（update-result で作り直す）")
        return
    try:
        actual = render_result(releases.connect(tag), sql, tag)
    except Unavailable:
        return  # 未検査としてまとめて表示する
    except duckdb.Error as e:
        r.error(
            f"リリース {tag} の DB で実行できません: {str(e).splitlines()[0]}\n"
            "    スキーマの変更に追従した場合は update-result --release latest で版を進めてください"
        )
        return
    expected = result_path.read_text(encoding="utf-8")
    if actual == expected:
        return
    diff = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(), "result.json", "実行結果", lineterm="", n=0))
    shown = diff[:DIFF_LINES] + ([f"…（残り {len(diff) - DIFF_LINES} 行）"] if len(diff) > DIFF_LINES else [])
    r.error(
        f"結果が result.json と違います（リリース {tag}）。意図した変更なら update-result で作り直してください\n"
        + "\n".join(f"    {line}" for line in shown)
    )


# ---------------------------------------------------------------- コマンド
def resolve_targets(paths: list[str]) -> list[Path]:
    if not paths:
        return sorted(p for p in QUERIES_DIR.iterdir() if p.is_dir())
    targets = []
    for p in map(Path, paths):
        p = p.resolve()
        d = p if p.is_dir() else p.parent
        if d.parent != QUERIES_DIR:
            sys.exit(f"queries/<description>/ 配下のパスを指定してください: {p}")
        if d not in targets:
            targets.append(d)
    return targets


def cmd_check(args) -> int:
    schema_validator = Draft202012Validator(json.loads(SCHEMA_FILE.read_text(encoding="utf-8")))
    # 飛ばした段階と、その理由
    skipped: dict[str, str] = {}

    known_tables: set[str] = set()
    if SQLITE_DB.exists():
        with sqlite3.connect(f"file:{SQLITE_DB}?mode=ro", uri=True) as conn:
            known_tables = {n for (n,) in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}
    else:
        skipped["SQLite"] = f"{SQLITE_DB.name} がありません"
    duck = None
    if DUCKDB_DB.exists():
        duck = duckdb.connect(str(DUCKDB_DB), read_only=True)
    else:
        skipped["DuckDB"] = f"{DUCKDB_DB.name} がありません"
    releases = ReleaseDatabases()

    failed = 0
    targets = resolve_targets(args.paths)
    for d in targets:
        r = Result(d)
        if not d.is_dir():
            r.error("ディレクトリがありません")
        elif check_files(r, d):
            meta_path = d / "meta.json"
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                r.error(f"meta.json が JSON として不正です: {e}")
                meta = None
            sql = (d / "query.sql").read_text(encoding="utf-8")
            if meta is not None:
                check_meta(r, d, meta, schema_validator)
            check_sql_style(r, sql)
            if SQLITE_DB.exists():
                result = run_sql(r, sql, known_tables)
                if result is not None and isinstance(meta, dict):
                    read_tables, columns, rows = result
                    check_tables(r, meta_path, meta, read_tables, args.fix)
                    if isinstance(meta.get("checks"), dict):
                        check_result(r, meta["checks"], columns, rows)
            if duck is not None:
                check_duckdb(r, duck, sql)
            check_snapshot(r, d, sql, releases, args.strict)

        rel = d.relative_to(ROOT)
        status = "FAIL" if r.errors else "PASS"
        suffix = f" ({'; '.join(r.notes)})" if r.notes else ""
        print(f"{status}: {rel}{suffix}")
        for e in r.errors:
            print(f"  - {e}")
        failed += bool(r.errors)

    for tag, reason in releases.unavailable.items():
        skipped[f"result.json（リリース {tag}）"] = reason
    print(f"\n{len(targets) - failed}/{len(targets)} passed")
    for stage, reason in skipped.items():
        print(f"未検査: {stage}（{reason}）")
    return 1 if failed or (args.strict and skipped) else 0


def cmd_update_result(args) -> int:
    releases = ReleaseDatabases()
    failed = 0
    try:
        release = latest_release() if args.release == "latest" else args.release
        for d in resolve_targets(args.paths):
            if not (d / "query.sql").exists():
                continue
            sql = (d / "query.sql").read_text(encoding="utf-8")
            result_path = d / RESULT_FILE
            tag = recorded_release(result_path) if result_path.exists() else None
            if release or not tag:
                tag = release or (release := latest_release())
            try:
                text = render_result(releases.connect(tag), sql, tag)
            except duckdb.Error as e:
                print(f"FAIL: {d.relative_to(ROOT)}\n  - リリース {tag} の DB で実行できません: {str(e).splitlines()[0]}")
                failed += 1
                continue
            if not result_path.exists() or result_path.read_text(encoding="utf-8") != text:
                result_path.write_text(text, encoding="utf-8")
                print(f"更新: {d.relative_to(ROOT)}（リリース {tag}）")
    except Unavailable as e:
        sys.exit(f"リリースの DB を用意できません: {e}")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="クエリを検査する")
    check.add_argument("paths", nargs="*", help="クエリのディレクトリまたはその中のファイル（省略時は全件）")
    check.add_argument("--fix", action="store_true", help="meta.json の tables を実際の参照テーブルで書き換える")
    check.add_argument("--strict", action="store_true", help="飛ばした段階や result.json のないクエリがあれば失敗にする（CI 用）")
    check.set_defaults(func=cmd_check)

    update = sub.add_parser("update-result", help="result.json を作り直す")
    update.add_argument("paths", nargs="*", help="クエリのディレクトリまたはその中のファイル（省略時は全件）")
    update.add_argument("--release", help="結果を作るリリースのタグ（latest で最新）。省略時は result.json の版のまま")
    update.set_defaults(func=cmd_update_result)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
