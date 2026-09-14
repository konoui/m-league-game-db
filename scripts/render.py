#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""queries/ から公開用の query-examples/*.md と query-examples/README.md を生成する。

usage: uv run scripts/render.py [--check]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUERIES_DIR = ROOT / "queries"
OUT_DIR = ROOT / "query-examples"


def render_query(d: Path) -> str:
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    sql = (d / "query.sql").read_text(encoding="utf-8").strip()
    lines = [
        "## 説明",
        meta["description"],
        "",
        "## SQL クエリ",
        "```sql",
        sql,
        "```",
        "",
        "## 参照テーブル",
        *[f"- {t}" for t in meta["tables"]],
        "",
    ]
    return "\n".join(lines)


def render_readme(names: list[str]) -> str:
    lines = ["# SQL クエリ例", ""]
    lines += [f"- [{n}](./{n}.md)" for n in names]
    return "\n".join(lines) + "\n"


def build() -> dict[str, str]:
    dirs = sorted(p for p in QUERIES_DIR.iterdir() if p.is_dir())
    files = {f"{d.name}.md": render_query(d) for d in dirs}
    files["README.md"] = render_readme([d.name for d in dirs])
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="生成物が最新か確認するだけで書き込まない")
    args = ap.parse_args()

    expected = build()
    actual = {p.name: p.read_text(encoding="utf-8") for p in OUT_DIR.glob("*.md")} if OUT_DIR.exists() else {}

    changed = sorted(n for n, c in expected.items() if actual.get(n) != c)
    stale = sorted(set(actual) - set(expected))

    if args.check:
        for n in changed:
            print(f"outdated: query-examples/{n}")
        for n in stale:
            print(f"stale: query-examples/{n}")
        if changed or stale:
            sys.exit("query-examples/ が queries/ と一致しません。uv run scripts/render.py を実行してください")
        print("query-examples/ is up to date")
        return

    OUT_DIR.mkdir(exist_ok=True)
    for n in changed:
        (OUT_DIR / n).write_text(expected[n], encoding="utf-8")
        print(f"write: query-examples/{n}")
    for n in stale:
        (OUT_DIR / n).unlink()
        print(f"remove: query-examples/{n}")


if __name__ == "__main__":
    main()
