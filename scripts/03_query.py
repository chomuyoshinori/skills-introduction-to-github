#!/usr/bin/env python3
"""④ 質問 → 関連箇所を検索 → Claude が出典付きで回答。

使い方:
    python scripts/03_query.py "ストレスと記憶の関係は？"
    python scripts/03_query.py            # 対話モード（空行/quit で終了）

出典付き・ハルシネーション抑制つき。検索した抜粋に無いことは答えさせない。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import load_config, env_or_die  # noqa: E402

# 02_index.py の部品を再利用
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "indexer", str(Path(__file__).resolve().parent / "02_index.py"))
indexer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(indexer)  # type: ignore

ANSWER_SYSTEM = (
    "あなたは蔵書アシスタントです。以下のルールを厳守してください。\n"
    "1. 回答は、提示された【抜粋】に書かれている内容のみを根拠にする。\n"
    "2. 抜粋に答えが無い場合は『蔵書の中に該当箇所が見つかりませんでした』と正直に言う。\n"
    "3. 主張ごとに、根拠にした抜粋の出典（書名 p.ページ）を文中または末尾に示す。\n"
    "4. 推測で補わない。抜粋の範囲を超える一般論は付け足さない。"
)


def search(question: str, cfg: dict, embedder, collection):
    q_emb = embedder.embed_query(question)
    res = collection.query(query_embeddings=[q_emb], n_results=cfg["query"]["top_k"])
    hits = []
    for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
        hits.append({"text": doc, "title": meta.get("title", meta.get("slug")),
                     "page": meta.get("page")})
    return hits


def build_context(hits) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"【抜粋{i}】（出典: {h['title']} p.{h['page']}）\n{h['text']}")
    return "\n\n".join(blocks)


def answer(question: str, cfg: dict, embedder, collection) -> None:
    import anthropic
    hits = search(question, cfg, embedder, collection)
    if not hits:
        print("蔵書がまだ索引されていないか、該当が見つかりませんでした。")
        return
    context = build_context(hits)
    user = f"{context}\n\n----\n上記の抜粋だけを根拠に、質問に出典付きで答えてください。\n質問: {question}"

    client = anthropic.Anthropic()
    print("\n--- 回答 ---")
    with client.messages.stream(
        model=cfg["query"]["model"],
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=ANSWER_SYSTEM,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n\n--- 参照した抜粋 ---")
    for i, h in enumerate(hits, 1):
        print(f"  {i}. {h['title']} p.{h['page']}")
    print()


def main() -> None:
    cfg = load_config()
    env_or_die("ANTHROPIC_API_KEY")
    embedder = indexer.Embedder(cfg)
    collection = indexer.get_collection(cfg)

    args = sys.argv[1:]
    if args:
        answer(" ".join(args), cfg, embedder, collection)
        return

    print("対話モード。質問を入力してください（空行または quit で終了）。")
    while True:
        try:
            q = input("\n質問> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q or q.lower() in {"quit", "exit"}:
            break
        answer(q, cfg, embedder, collection)


if __name__ == "__main__":
    main()
