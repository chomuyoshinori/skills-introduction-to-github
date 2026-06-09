#!/usr/bin/env python3
"""① OCR: PDF → ページ画像 → テキスト（書名・ページ番号付き）。

縦書き和書に強いバックエンドで取り直す。インターフェースは
「ページ画像(PNG bytes) → テキスト」で統一し、backend を差し替え可能。

使い方:
    python scripts/01_ocr.py                 # books_dir 内の全PDFを処理（未処理のみ）
    python scripts/01_ocr.py path/to/a.pdf   # 1ファイルだけ処理

出力:
    work_dir/text/<slug>/0001.txt ...        # ページごと（レジューム用）
    work_dir/text/<slug>.jsonl               # {"page", "text"} を集約

設定: config/config.yaml の ocr.* を参照。
注意: Document AI バックエンドは google-cloud-documentai の標準呼び出し。
      最新SDK仕様は本番投入前に確認すること。Claude バックエンドは検証済み。
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import (  # noqa: E402
    load_config, slugify, book_text_dir, upsert_catalog, env_or_die,
)

OCR_SYSTEM = (
    "あなたは日本語OCRエンジンです。渡された書籍ページの画像から本文テキストを"
    "正確に書き起こしてください。縦書きは正しい読み順（右上→左下）で。"
    "ルビ・ノンブル・ヘッダー/フッターの飾り・図版のキャプション番号は本文に混ぜない。"
    "本文以外の説明や前置きは一切出力せず、本文テキストのみを返してください。"
)


def render_pages(pdf_path: Path, dpi: int):
    """PDFの各ページを PNG bytes にして yield する。"""
    doc = fitz.open(pdf_path)
    try:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for i in range(doc.page_count):
            pix = doc.load_page(i).get_pixmap(matrix=mat)
            yield i + 1, pix.tobytes("png")
    finally:
        doc.close()


# ---- バックエンド: 画像 bytes -> テキスト ----

def ocr_claude(png: bytes, cfg: dict) -> str:
    import anthropic
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY を読む
    b64 = base64.standard_b64encode(png).decode()
    resp = client.messages.create(
        model=cfg["ocr"]["claude_model"],
        max_tokens=8000,
        system=OCR_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                {"type": "text", "text": "このページの本文を書き起こしてください。"},
            ],
        }],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def ocr_documentai(png: bytes, cfg: dict) -> str:
    # google-cloud-documentai を使用。最新仕様は要確認。
    from google.cloud import documentai
    d = cfg["ocr"]["documentai"]
    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(d["project_id"], d["location"], d["processor_id"])
    raw = documentai.RawDocument(content=png, mime_type="image/png")
    result = client.process_document(
        request=documentai.ProcessRequest(name=name, raw_document=raw)
    )
    return (result.document.text or "").strip()


BACKENDS = {"claude": ocr_claude, "documentai": ocr_documentai}


def process_pdf(pdf_path: Path, cfg: dict) -> None:
    slug = slugify(pdf_path.name)
    out_dir = book_text_dir(cfg, slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    backend = BACKENDS[cfg["ocr"]["backend"]]
    dpi = cfg["ocr"]["dpi"]

    print(f"▶ {pdf_path.name}  (slug={slug}, backend={cfg['ocr']['backend']})")
    n_pages = 0
    for page_no, png in render_pages(pdf_path, dpi):
        n_pages = page_no
        page_file = out_dir / f"{page_no:04d}.txt"
        if page_file.exists() and page_file.stat().st_size > 0:
            continue  # レジューム: 済みページはスキップ
        text = backend(png, cfg)
        page_file.write_text(text, encoding="utf-8")
        print(f"   p.{page_no} ({len(text)}字)")

    # ページを jsonl に集約
    jsonl = book_text_dir(cfg, slug).parent / f"{slug}.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for pf in sorted(out_dir.glob("*.txt")):
            page = int(pf.stem)
            f.write(json.dumps({"page": page, "text": pf.read_text(encoding="utf-8")},
                               ensure_ascii=False) + "\n")

    upsert_catalog(slug, title=slug, pdf_path=pdf_path.name,
                   pages=n_pages, ocr_status="done")
    print(f"✓ {slug}: {n_pages}ページ OCR完了\n")


def main() -> None:
    cfg = load_config()
    if cfg["ocr"]["backend"] == "claude":
        env_or_die("ANTHROPIC_API_KEY")

    args = sys.argv[1:]
    if args:
        pdfs = [Path(a).expanduser() for a in args]
    else:
        pdfs = sorted(cfg["paths"]["books_dir"].glob("**/*.pdf"))

    if not pdfs:
        raise SystemExit("処理対象のPDFが見つかりません。books_dir を確認してください。")

    print(f"対象: {len(pdfs)}冊\n")
    for pdf in pdfs:
        try:
            process_pdf(pdf, cfg)
        except Exception as e:  # 1冊失敗しても全体は続行
            print(f"✗ {pdf.name}: {e}\n")


if __name__ == "__main__":
    main()
