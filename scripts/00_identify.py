#!/usr/bin/env python3
"""⓪ 識別・分類（非破壊）: 各PDFの数ページだけ読んで書誌情報を抽出し、
knowledge/catalog.csv に書き出す。

★ 実ファイルは一切リネーム・移動しない（原本そのまま方針）。
   抽出した「書名・著者・出版社・刊行年・ジャンル」をカタログに整備するだけ。

安く済ませる工夫:
  - まずPDFの埋め込みテキスト（表紙・標題紙・奥付）を無料で抽出
  - テキストが取れなければ、先頭2ページ＋最終1ページだけ画像化してClaude visionで読む
  - 全ページは読まない（識別に必要なページだけ）

使い方:
    python scripts/00_identify.py                # 未識別のPDFを全部
    python scripts/00_identify.py path/to/a.pdf  # 1冊だけ
    python scripts/00_identify.py --force        # 識別済みも再実行

出力: knowledge/catalog.csv（identify_status=done を立てる）
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import (  # noqa: E402
    load_config, slugify, read_catalog, upsert_catalog, env_or_die,
)

SYSTEM = (
    "あなたは図書館の目録担当です。提示された書籍の表紙・標題紙・奥付（コロフォン）から、"
    "書誌情報を抽出してください。縦書きにも対応。分からない項目は空文字にし、"
    "推測で埋めないこと。confidence は抽出全体の確信度。"
    "genre は内容に基づく簡潔なジャンル（例: 神経科学, 哲学, 経営, 小説, 料理 など）。"
)

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "author": {"type": "string"},
        "publisher": {"type": "string"},
        "year": {"type": "string"},
        "genre": {"type": "string"},
        "language": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["title", "author", "publisher", "year", "genre", "language", "confidence"],
    "additionalProperties": False,
}

# 埋め込みテキストがこの文字数以上あれば、画像を使わずテキストだけで識別する
TEXT_THRESHOLD = 200


def gather_clues(pdf_path: Path, dpi: int):
    """識別の手がかりを集める。
    戻り値: (page_count, embedded_text, [png_bytes,...])
    画像はテキストが足りないときだけ作る。
    """
    doc = fitz.open(pdf_path)
    try:
        n = doc.page_count
        front = range(0, min(3, n))            # 表紙・標題紙まわり
        back = range(max(0, n - 2), n)         # 奥付まわり
        idx = sorted(set(front) | set(back))

        texts = []
        meta = doc.metadata or {}
        if meta.get("title"):
            texts.append(f"[PDFメタ title] {meta['title']}")
        if meta.get("author"):
            texts.append(f"[PDFメタ author] {meta['author']}")
        for i in idx:
            t = doc.load_page(i).get_text().strip()
            if t:
                texts.append(f"[p.{i + 1}]\n{t}")
        embedded = "\n\n".join(texts)

        images = []
        if len(embedded) < TEXT_THRESHOLD:
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            for i in sorted(set([0, min(1, n - 1), n - 1])):
                pix = doc.load_page(i).get_pixmap(matrix=mat)
                images.append(pix.tobytes("png"))
        return n, embedded, images
    finally:
        doc.close()


def extract_metadata(embedded: str, images, cfg: dict) -> dict:
    import anthropic
    client = anthropic.Anthropic()

    content = []
    if embedded:
        content.append({"type": "text",
                        "text": f"以下は書籍から抽出したテキストです:\n\n{embedded}"})
    for png in images:
        b64 = base64.standard_b64encode(png).decode()
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64}})
    content.append({"type": "text", "text": "この本の書誌情報をJSONで返してください。"})

    resp = client.messages.create(
        model=cfg["ocr"]["identify_model"],
        max_tokens=1000,
        system=SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


def identify_pdf(pdf_path: Path, cfg: dict) -> None:
    slug = slugify(pdf_path.name)
    n, embedded, images = gather_clues(pdf_path, cfg["ocr"]["dpi"])
    src = "埋め込みテキスト" if not images else f"画像{len(images)}枚"
    print(f"▶ {pdf_path.name}  ({src}, {n}p)")

    meta = extract_metadata(embedded, images, cfg)
    upsert_catalog(
        slug,
        title=meta.get("title") or slug,
        author=meta.get("author", ""),
        publisher=meta.get("publisher", ""),
        year=meta.get("year", ""),
        genre=meta.get("genre", ""),
        language=meta.get("language", ""),
        pages=n,
        confidence=meta.get("confidence", ""),
        identify_status="done",
        pdf_path=pdf_path.name,
    )
    print(f"  ✓ 『{meta.get('title','?')}』 / {meta.get('author','?')} "
          f"／{meta.get('genre','?')} [確信度 {meta.get('confidence','?')}]\n")


def main() -> None:
    cfg = load_config()
    env_or_die("ANTHROPIC_API_KEY")

    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]

    if args:
        pdfs = [Path(a).expanduser() for a in args]
    else:
        pdfs = sorted(cfg["paths"]["books_dir"].glob("**/*.pdf"))

    if not pdfs:
        raise SystemExit("PDFが見つかりません。books_dir を確認してください。")

    catalog = read_catalog()
    todo = []
    for pdf in pdfs:
        slug = slugify(pdf.name)
        if not force and catalog.get(slug, {}).get("identify_status") == "done":
            continue
        todo.append(pdf)

    print(f"識別対象: {len(todo)}冊 / 全{len(pdfs)}冊\n")
    for pdf in todo:
        try:
            identify_pdf(pdf, cfg)
        except Exception as e:  # 1冊失敗しても続行
            print(f"  ✗ {pdf.name}: {e}\n")

    print("完了。knowledge/catalog.csv を開いて、誤判定の修正と priority(high/mid/low) の記入を。")


if __name__ == "__main__":
    main()
