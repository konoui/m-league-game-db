#!/usr/bin/env python3
"""Stop hook: 作業を終える前に、変更したクエリの検証と query-examples/ の生成漏れを確認する。

queries/ などに未コミットの変更がなければ何もしない。PLAN.md だけのディレクトリ（計画の承認待ち）は検証しない。
失敗時は exit 2 で結果を Claude に返し、修正を続けさせる。
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCHED = ["queries", "query-examples", "schema", "scripts/validate.py", "scripts/render.py"]
# これらが変わったら全クエリを検証する
VALIDATE_ALL_TRIGGERS = ("schema/", "scripts/validate.py")


def is_planning(d: Path) -> bool:
    return not (d / "meta.json").exists() and not (d / "query.sql").exists()


def changed_paths() -> list[str]:
    out = subprocess.run(
        ["git", "status", "--porcelain", "-uall", "-z", "--", *WATCHED],
        capture_output=True, text=True, cwd=ROOT, check=True,
    ).stdout
    paths = []
    entries = iter(out.split("\0"))
    for entry in entries:
        if not entry:
            continue
        status, path = entry[:2], entry[3:]
        if "R" in status or "C" in status:
            next(entries, None)  # リネーム元のパス
        paths.append(path)
    return paths


def main():
    payload = json.load(sys.stdin)
    # 直前の Stop hook で差し戻した後は、無限ループを避けるため止めない
    if payload.get("stop_hook_active"):
        return

    paths = changed_paths()
    if not paths:
        return

    validate = ["uv", "run", "--quiet", "scripts/validate.py"]
    if not (ROOT / "database.sqlite3").exists():
        validate.append("--no-run")
    if any(p.startswith(VALIDATE_ALL_TRIGGERS) for p in paths):
        dirs = [str(d.relative_to(ROOT)) for d in sorted((ROOT / "queries").iterdir()) if d.is_dir()]
    else:
        dirs = sorted({str(Path(*Path(p).parts[:2])) for p in paths if p.startswith("queries/")})
    # PLAN.md だけのディレクトリは計画の承認待ちなので検証しない
    dirs = [d for d in dirs if (ROOT / d).is_dir() and not is_planning(ROOT / d)]
    validate = validate + dirs if dirs else None

    failures = []
    for cmd in filter(None, [validate, ["uv", "run", "--quiet", "scripts/render.py", "--check"]]):
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if proc.returncode != 0:
            failures.append(f"$ {' '.join(cmd)}\n{proc.stdout}{proc.stderr}")

    if failures:
        print("作業を終える前に次の問題を解消してください。\n\n" + "\n".join(failures), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
