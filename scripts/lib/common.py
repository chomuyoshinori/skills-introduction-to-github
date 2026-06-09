"""共通処理: 設定読込・パス解決・蔵書カタログの読み書き。

全スクリプト（01_ocr.py / 02_index.py / 03_query.py）から import して使う。
"""
from __future__ import annotations

import csv
import os
import re
import unicodedata
from pathlib import Path

import yaml

# scripts/ の1つ上 = リポジトリルート
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"
CATALOG_PATH = REPO_ROOT / "knowledge" / "catalog.csv"

CATALOG_FIELDS = [
    "slug",        # ファイル名から作る一意なID
    "title",       # 書名（人が編集）
    "author",      # 著者（人が編集）
    "pdf_path",    # 元PDFのパス（books_dir からの相対）
    "pages",       # ページ数
    "ocr_status",  # "", "done"
    "index_status",# "", "done"
    "note",        # 自由メモ
]


def load_config() -> dict:
    """config/config.yaml を読む。無ければ例を案内して終了。"""
    if not CONFIG_PATH.exists():
        raise SystemExit(
            f"設定ファイルがありません: {CONFIG_PATH}\n"
            f"config/config.example.yaml をコピーして config.yaml を作り、編集してください。"
        )
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # パスを Path に
    for key in ("books_dir", "work_dir", "db_dir"):
        cfg["paths"][key] = Path(cfg["paths"][key]).expanduser()
    return cfg


def slugify(name: str) -> str:
    """書名・ファイル名から安全な slug を作る（日本語はそのまま、記号類を _ に）。"""
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"\.pdf$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[\s/\\:*?\"<>|]+", "_", name).strip("_")
    return name or "untitled"


def text_dir(cfg: dict) -> Path:
    return cfg["paths"]["work_dir"] / "text"


def book_text_dir(cfg: dict, slug: str) -> Path:
    return text_dir(cfg) / slug


# ---- 蔵書カタログ ----

def read_catalog() -> dict[str, dict]:
    """slug -> row の辞書で返す。"""
    rows: dict[str, dict] = {}
    if CATALOG_PATH.exists():
        with open(CATALOG_PATH, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                rows[row["slug"]] = row
    return rows


def write_catalog(rows: dict[str, dict]) -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CATALOG_FIELDS)
        w.writeheader()
        for slug in sorted(rows):
            w.writerow({k: rows[slug].get(k, "") for k in CATALOG_FIELDS})


def upsert_catalog(slug: str, **fields) -> None:
    """カタログの1行を作成/更新して保存する。"""
    rows = read_catalog()
    row = rows.get(slug, {"slug": slug})
    row.update({k: str(v) for k, v in fields.items() if v is not None})
    rows[slug] = row
    write_catalog(rows)


def env_or_die(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise SystemExit(f"環境変数 {name} が未設定です。export {name}=... してください。")
    return val
