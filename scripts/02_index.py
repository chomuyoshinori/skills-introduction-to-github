#!/usr/bin/env python3
"""②③ チャンク分割 → 埋め込み → ベクトルDB(Chroma) 登録。

使い方:
    python scripts/02_index.py            # OCR済みで未索引の本をすべて登録
    python scripts/02_index.py <slug>     # 指定slugだけ登録（再登録は上書き）

埋め込みは config の embedding.provider で切替（local / openai）。
レジューム: index_status=done の本はスキップ。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import (  # noqa: E402
    load_config, read_catalog, upsert_catalog, text_dir, env_or_die,
)


# ---- チャンク分割 ----

def chunk_text(text: str, size: int, overlap: int):
    text = text.strip()
    if not text:
        return
    step = max(1, size - overlap)
    for start in range(0, len(text), step):
        piece = text[start:start + size].strip()
        if piece:
            yield piece
        if start + size >= len(text):
            break


# ---- 埋め込み（プロバイダ切替） ----

class Embedder:
    def __init__(self, cfg: dict):
        self.provider = cfg["embedding"]["provider"]
        if self.provider == "local":
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(cfg["embedding"]["local_model"])
        elif self.provider == "openai":
            import openai
            env_or_die("OPENAI_API_KEY")
            self.client = openai.OpenAI()
            self.model_name = cfg["embedding"]["openai_model"]
        else:
            raise SystemExit(f"未知の embedding.provider: {self.provider}")

    def _prefix(self, texts, kind: str):
        # e5系は passage:/query: 接頭辞が必要
        if self.provider == "local" and "e5" in str(getattr(self.model, "model_card_data", "")) + self.provider:
            return [f"{kind}: {t}" for t in texts]
        return list(texts)

    def embed_passages(self, texts):
        if self.provider == "local":
            inputs = [f"passage: {t}" for t in texts]
            return self.model.encode(inputs, normalize_embeddings=True).tolist()
        resp = self.client.embeddings.create(model=self.model_name, input=list(texts))
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str):
        if self.provider == "local":
            return self.model.encode([f"query: {text}"], normalize_embeddings=True)[0].tolist()
        resp = self.client.embeddings.create(model=self.model_name, input=[text])
        return resp.data[0].embedding


def get_collection(cfg: dict):
    import chromadb
    client = chromadb.PersistentClient(path=str(cfg["paths"]["db_dir"]))
    return client.get_or_create_collection(
        name=cfg.get("collection", "books"),
        metadata={"hnsw:space": "cosine"},
    )


def index_book(slug: str, cfg: dict, embedder: Embedder, collection) -> int:
    jsonl = text_dir(cfg) / f"{slug}.jsonl"
    if not jsonl.exists():
        print(f"  ! {slug}: OCR集約ファイルが無い（先に 01_ocr.py を）")
        return 0

    catalog = read_catalog()
    title = catalog.get(slug, {}).get("title", slug)
    size = cfg["chunk"]["size"]
    overlap = cfg["chunk"]["overlap"]

    ids, docs, metas = [], [], []
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        page = rec["page"]
        for ci, piece in enumerate(chunk_text(rec["text"], size, overlap)):
            ids.append(f"{slug}:{page:04d}:{ci:03d}")
            docs.append(piece)
            metas.append({"slug": slug, "title": title, "page": page, "chunk": ci})

    if not docs:
        print(f"  - {slug}: テキストなし、スキップ")
        return 0

    # 既存（再登録時）を消してから入れ直す
    collection.delete(where={"slug": slug})
    # バッチで埋め込み・登録
    BATCH = 64
    for i in range(0, len(docs), BATCH):
        embs = embedder.embed_passages(docs[i:i + BATCH])
        collection.add(ids=ids[i:i + BATCH], documents=docs[i:i + BATCH],
                       metadatas=metas[i:i + BATCH], embeddings=embs)
    upsert_catalog(slug, index_status="done")
    print(f"  ✓ {slug}: {len(docs)} チャンク登録")
    return len(docs)


def main() -> None:
    cfg = load_config()
    embedder = Embedder(cfg)
    collection = get_collection(cfg)

    catalog = read_catalog()
    args = sys.argv[1:]
    if args:
        targets = args
    else:
        targets = [s for s, r in catalog.items()
                   if r.get("ocr_status") == "done" and r.get("index_status") != "done"]

    if not targets:
        print("索引対象なし（OCR済みで未索引の本がありません）")
        return

    print(f"索引対象: {len(targets)}冊")
    total = 0
    for slug in targets:
        total += index_book(slug, cfg, embedder, collection)
    print(f"\n完了: 合計 {total} チャンクを登録しました。")


if __name__ == "__main__":
    main()
