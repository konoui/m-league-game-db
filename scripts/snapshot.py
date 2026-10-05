#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["duckdb>=1.5.5"]
# ///
"""queries/<description>/result.json（固定した版の DB での実行結果）を検査・更新する。

usage: uv run scripts/snapshot.py [--update] [--release TAG] [QUERY_DIR_OR_FILE ...]

クエリを書き換えたときに結果が変わったかどうかを、result.json の差分として見えるようにする。
DB は日々更新されるので、結果は result.json の db に書いたリリース（DuckDB 版）で固定する。
そのリリースの DB は初回に gh でダウンロードし、.cache/snapshot-db/<タグ>/ に置く。

- 引数なし: result.json が、そこに書かれた版の DB での実行結果と一致するか検査する
- --update: result.json を作り直す。すでにあるクエリはその版のまま、ないクエリは最新のリリースで作る
- --update --release TAG: 指定したリリース（latest で最新）に版を進めて作り直す

validate.py が見るのは最新の DB で不変条件が成り立つかで、こちらは同じ DB で結果が変わっていないかを見る。
"""

import argparse
import datetime
import decimal
import difflib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
QUERIES = ROOT / "queries"
CACHE = ROOT / ".cache" / "snapshot-db"
RESULT_FILE = "result.json"
ASSET = "duckdb.zip"
# 差分を表示する行数の上限
DIFF_LINES = 30


def resolve_targets(paths: list[str]) -> list[Path]:
    if not paths:
        return sorted(d for d in QUERIES.iterdir() if d.is_dir() and (d / "query.sql").exists())
    out = []
    for p in paths:
        path = Path(p).resolve()
        d = path if path.is_dir() else path.parent
        if d.parent != QUERIES:
            sys.exit(f"queries/<description>/ 配下のパスを指定してください: {p}")
        out.append(d)
    return sorted(set(out))


def gh(*args: str) -> str:
    try:
        return subprocess.run(["gh", *args], capture_output=True, text=True, cwd=ROOT, check=True).stdout
    except FileNotFoundError:
        sys.exit("gh コマンドがありません（リリースの DB を取得するのに使います）")
    except subprocess.CalledProcessError as e:
        sys.exit(f"gh {' '.join(args)} に失敗しました: {e.stderr.strip()}")


def latest_release() -> str:
    return gh("release", "view", "--json", "tagName", "--jq", ".tagName").strip()


def database(tag: str) -> Path:
    """リリース tag の DuckDB 版 DB のパスを返す。手元になければダウンロードする。"""
    d = CACHE / tag
    db = d / "database.duckdb"
    if db.exists():
        return db
    d.mkdir(parents=True, exist_ok=True)
    print(f"リリース {tag} の {ASSET} をダウンロードします", file=sys.stderr)
    gh("release", "download", tag, "--pattern", ASSET, "--dir", str(d), "--clobber")
    with zipfile.ZipFile(d / ASSET) as z:
        name = next(n for n in z.namelist() if n.endswith(".duckdb"))
        tmp = d / "database.duckdb.tmp"
        tmp.write_bytes(z.read(name))
    tmp.replace(db)
    (d / ASSET).unlink()
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


def run(conn: duckdb.DuckDBPyConnection, sql: str, tag: str) -> str:
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
    if not result_path.exists():
        return None
    try:
        db = json.loads(result_path.read_text(encoding="utf-8")).get("db")
    except (json.JSONDecodeError, AttributeError):
        return None
    return db if isinstance(db, str) and db else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="クエリのディレクトリまたはその中のファイル（省略時は全件）")
    ap.add_argument("--update", action="store_true", help="result.json を作り直す")
    ap.add_argument("--release", help="--update で使うリリースのタグ（latest で最新）。省略時は result.json の版のまま")
    args = ap.parse_args()
    if args.release and not args.update:
        ap.error("--release は --update と一緒に指定してください")

    release = latest_release() if args.release == "latest" else args.release
    conns: dict[str, duckdb.DuckDBPyConnection] = {}

    def connect(tag: str) -> duckdb.DuckDBPyConnection:
        if tag not in conns:
            conns[tag] = duckdb.connect(str(database(tag)), read_only=True)
        return conns[tag]

    failed = 0
    targets = resolve_targets(args.paths)
    for d in targets:
        sql = (d / "query.sql").read_text(encoding="utf-8")
        result_path = d / RESULT_FILE
        tag = recorded_release(result_path)

        if args.update:
            if release or not tag:
                tag = release or (release := latest_release())
            try:
                text = run(connect(tag), sql, tag)
            except duckdb.Error as e:
                print(f"NG   {d.name}\n       リリース {tag} の DB で実行できません: {str(e).splitlines()[0]}")
                failed += 1
                continue
            if not result_path.exists() or result_path.read_text(encoding="utf-8") != text:
                result_path.write_text(text, encoding="utf-8")
                print(f"更新 {d.name}（{tag}）")
            continue

        if not tag:
            print(f"NG   {d.name}\n       result.json がないか、db が読めません（--update で作成）")
            failed += 1
            continue
        try:
            actual = run(connect(tag), sql, tag)
        except duckdb.Error as e:
            print(f"NG   {d.name}\n       リリース {tag} の DB で実行できません: {str(e).splitlines()[0]}")
            print("       スキーマの変更に追従した場合は --update --release latest で版を進めてください")
            failed += 1
            continue
        expected = result_path.read_text(encoding="utf-8")
        if actual == expected:
            continue
        failed += 1
        print(f"NG   {d.name}\n       結果が result.json と違います（リリース {tag}）。意図した変更なら --update で作り直してください")
        diff = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(), "result.json", "実行結果", lineterm="", n=0))
        for line in diff[:DIFF_LINES]:
            print(f"       {line}")
        if len(diff) > DIFF_LINES:
            print(f"       …（残り {len(diff) - DIFF_LINES} 行）")

    if args.update:
        print(f"\n{len(targets)} 件中 {len(targets) - failed} 件の result.json を作成・確認した")
    else:
        print(f"\n{len(targets)} 件中 {len(targets) - failed} 件が result.json と一致した")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
