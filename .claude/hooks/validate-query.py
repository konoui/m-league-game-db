#!/usr/bin/env python3
"""PostToolUse hook: queries/<description>/ 配下を編集したら、そのクエリを validate.py で検証する。

meta.json がまだないディレクトリは作成途中とみなして検証しない（Stop hook で検証される）。
失敗時は exit 2 で検証結果を Claude に返す。
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUERIES_DIR = ROOT / "queries"


def main():
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        return
    path = Path(file_path).resolve()
    if path.parent.parent != QUERIES_DIR or not (path.parent / "meta.json").exists():
        return

    cmd = ["uv", "run", "--quiet", str(ROOT / "scripts" / "validate.py"), str(path.parent)]
    if not (ROOT / "database.sqlite3").exists():
        cmd.append("--no-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        print(proc.stdout + proc.stderr, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
