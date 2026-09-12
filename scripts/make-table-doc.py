#!/usr/bin/env python3
"""table-doc.yaml から人間が読む用のテーブル定義ドキュメント（目次込み）を生成する。

使い方: uv run --quiet --with pyyaml python ./scripts/make-table-doc.py <table-doc.yaml> <出力先>
table-doc.yaml は m-converter が正とし、表形式のフォーマットはこのスクリプトが正。
make.sh から呼ばれる。
"""

import sys
import unicodedata

import yaml

HEADER = ["カラム名", "データ型", "NULL 許可", "説明"]
TOC_BEGIN = "<!-- TOC BEGIN -->"
TOC_END = "<!-- TOC END -->"


def width(text):
    """Markdown テーブルの整形に使う表示幅。全角文字は 2 とする。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, size):
    return text + " " * (size - width(text))


def slugify(text):
    """GitHub の見出しアンカーを生成する。"""
    s = text.lower().replace(" ", "-")
    return "".join(
        ch
        for ch in s
        if ch in ("-", "_") or unicodedata.category(ch).startswith(("L", "N"))
    )


def render_table(columns):
    rows = [HEADER]
    for c in columns:
        rows.append(
            [
                c["name"],
                c["type"],
                "YES" if c.get("nullable") else "NO",
                c["desc"],
            ]
        )
    widths = [max(width(row[i]) for row in rows) for i in range(len(HEADER))]
    out = ["| " + " | ".join(pad(v, w) for v, w in zip(rows[0], widths)) + " |"]
    out.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in rows[1:]:
        out.append("| " + " | ".join(pad(v, w) for v, w in zip(row, widths)) + " |")
    return out


def render_alert(kind, text):
    return [f"> [!{kind}]"] + [f"> {line}" for line in text.split("\n")] + [""]


def render_toc(doc):
    """## 以下の見出しから目次を生成する。"""
    out = [TOC_BEGIN, ""]
    for sec in doc["sections"]:
        out.append(f"{'  ' * (sec['level'] - 2)}- [{sec['heading']}](#{slugify(sec['heading'])})")
        for t in sec["tables"]:
            title = f"{t['name']}（{t['title']}）"
            out.append(f"{'  ' * (t['level'] - 2)}- [{title}](#{slugify(title)})")
    out += ["", TOC_END, ""]
    return out


def gen_doc(doc) -> str:
    out = [f"# {doc['title']}", ""] + render_toc(doc)
    for sec in doc["sections"]:
        out += [f"{'#' * sec['level']} {sec['heading']}", ""]
        for t in sec["tables"]:
            out += [f"{'#' * t['level']} {t['name']}（{t['title']}）", ""]
            if t.get("note"):
                out += render_alert("NOTE", t["note"])
            if t.get("important"):
                out += render_alert("IMPORTANT", t["important"])
            meta = []
            if t.get("primary_key"):
                label = "複合主キー" if len(t["primary_key"]) > 1 else "主キー"
                meta.append(f"**{label}**: {', '.join(t['primary_key'])}")
            if t.get("foreign_keys"):
                meta.append("**外部キー**: " + ", ".join(t["foreign_keys"]))
            if meta:
                out += meta + [""]
            out += render_table(t["columns"]) + [""]
    return "\n".join(out)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(gen_doc(doc))
    n_tables = sum(len(s["tables"]) for s in doc["sections"])
    print(f"generated {dst} ({n_tables} tables)")
