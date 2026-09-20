#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["duckdb>=1.5.5"]
# ///
"""queries/<description>/query.sql が DuckDB 版のデータベースでも実行できるか検証する。

usage: uv run scripts/validate-duckdb.py [--db FILE] [QUERY_DIR_OR_FILE ...]

SQLite 版の検証は validate.py が行う。こちらは DuckDB 固有の差だけを見る。
両方で通る SQL にしておきたいのは、どちらの配布物を使っても同じクエリ例が読めるようにするため。

つまずきやすいのは次の 2 つ。

- GROUP BY: SQLite は GROUP BY にない列の select を許すが、DuckDB は許さない。
  グループを一意に決める列 (p.id で束ねているときの p.name など) を GROUP BY に足す
- 関数の差: strftime は引数の順が逆になる。date は YYYY-MM-DD の文字列なので
  substr(date, 1, 4) のように、どちらでも同じ意味になる書き方にする
"""

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
QUERIES = ROOT / "queries"


def resolve_targets(paths: list[str]) -> list[Path]:
    if not paths:
        return sorted(d for d in QUERIES.iterdir() if d.is_dir())
    out = []
    for p in paths:
        path = Path(p).resolve()
        out.append(path.parent if path.is_file() else path)
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="クエリのディレクトリまたはその中のファイル（省略時は全件）")
    ap.add_argument("--db", default=str(ROOT / "database.duckdb"), help="DuckDB データベース")
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        sys.exit(f"データベースがありません: {db}")

    conn = duckdb.connect(str(db), read_only=True)
    failed = 0
    targets = resolve_targets(args.paths)
    for d in targets:
        sql_file = d / "query.sql"
        if not sql_file.exists():
            print(f"NG   {d.name}: query.sql がありません")
            failed += 1
            continue
        try:
            conn.execute(sql_file.read_text(encoding="utf-8")).fetchall()
        except Exception as e:
            print(f"NG   {d.name}")
            print(f"       {str(e).splitlines()[0]}")
            failed += 1

    print(f"\n{len(targets)} 件中 {len(targets) - failed} 件が DuckDB で実行できた")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
