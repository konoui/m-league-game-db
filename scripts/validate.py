#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jsonschema>=4"]
# ///
"""queries/<description>/ の query.sql と meta.json を検証する。

usage: uv run scripts/validate.py [--db FILE] [--no-run] [--fix] [QUERY_DIR_OR_FILE ...]
"""

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
QUERIES_DIR = ROOT / "queries"
SCHEMA_FILE = ROOT / "schema" / "meta.schema.json"
QUERY_FILES = {"query.sql", "meta.json"}
OPTIONAL_FILES = {"PLAN.md"}

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


def check_files(r: Result, d: Path) -> bool:
    names = {p.name for p in d.iterdir()}
    for missing in sorted(QUERY_FILES - names):
        r.error(f"{missing} がありません")
    for extra in sorted(names - QUERY_FILES - OPTIONAL_FILES):
        r.error(f"想定外のファイルです: {extra}（query.sql, meta.json, PLAN.md のみ置けます）")
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


def run_sql(r: Result, sql: str, db: Path, known_tables: set[str], timeout: float) -> tuple[set[str], list[str], list[tuple]] | None:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    read_tables: set[str] = set()
    denied: list[str] = []

    def authorizer(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ and arg1 in known_tables:
            read_tables.add(arg1)
        if action not in ALLOWED_ACTIONS:
            denied.append(str(action))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    deadline = time.monotonic() + timeout
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
            r.error(f"実行が {timeout:.0f} 秒を超えました")
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="クエリのディレクトリまたはその中のファイル（省略時は全件）")
    ap.add_argument("--db", default=str(ROOT / "database.sqlite3"), help="SQLite データベース")
    ap.add_argument("--no-run", action="store_true", help="SQL を実行しない（tables の照合も省略）")
    ap.add_argument("--fix", action="store_true", help="meta.json の tables を実際の参照テーブルで書き換える")
    ap.add_argument("--timeout", type=float, default=120, help="1 クエリの実行時間上限（秒）")
    args = ap.parse_args()

    schema_validator = Draft202012Validator(json.loads(SCHEMA_FILE.read_text(encoding="utf-8")))
    db = Path(args.db)
    run = not args.no_run
    if run and not db.exists():
        sys.exit(f"データベースがありません: {db}（--no-run で実行なしの検証のみ可能）")
    known_tables: set[str] = set()
    if run:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
            known_tables = {n for (n,) in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}

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
            if run:
                result = run_sql(r, sql, db, known_tables, args.timeout)
                if result is not None and isinstance(meta, dict):
                    read_tables, columns, rows = result
                    check_tables(r, meta_path, meta, read_tables, args.fix)
                    if isinstance(meta.get("checks"), dict):
                        check_result(r, meta["checks"], columns, rows)

        rel = d.relative_to(ROOT)
        status = "FAIL" if r.errors else "PASS"
        suffix = f" ({'; '.join(r.notes)})" if r.notes else ""
        print(f"{status}: {rel}{suffix}")
        for e in r.errors:
            print(f"  - {e}")
        failed += bool(r.errors)

    print(f"\n{len(targets) - failed}/{len(targets)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
