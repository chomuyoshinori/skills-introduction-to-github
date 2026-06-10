"""AI視覚レビューを学習の報酬に組み込む（docs/agents.md の Phase 1 実装）。

数値検査（プロポーション誤差・ポリ効率）だけでは「見た目の良さ」を評価できない。
そこで上位候補をレンダリングし、AI（agents/modeler.md の役割）が画像を採点、
そのスコアをエンジンスコアにブレンドして知識ベース（top_k / best / sweet spot）
を再ランクする。次回の optimizer 実行はこの更新済み知見から探索するため、
美的評価が探索方向にフィードバックされる。

使い方（2フェーズ）:
  # 1) 上位候補をレンダリングしてレビュー依頼を出力
  python scripts/learn/visual_review.py -- --asset assets/characters/goblin-warrior --top 4

  # 2) AI/人が learn/review_scores.json を書いたら、報酬にブレンドして知見を更新
  python scripts/learn/visual_review.py -- --asset assets/characters/goblin-warrior --apply

review_scores.json の形式:
  {"0": {"visual": 8, "notes": "シルエットが読みやすい"}, "1": {...}}
  visual は 0〜10。blended = engine_score + VISUAL_WEIGHT * visual
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.learn import lessons as L  # noqa: E402
from scripts.learn.optimizer import _load_asset_meta, _load_generator  # noqa: E402
from scripts.lib.viz import render_scene  # noqa: E402

VISUAL_WEIGHT = 2.0  # visual(0-10) → 最大 +20 点。美的評価が順位を入れ替えられる重み


def _parse_args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    args = {"asset": None, "top": 4, "apply": False, "res": 512, "recent": 0}
    it = iter(argv)
    for tok in it:
        if tok == "--asset":
            args["asset"] = next(it)
        elif tok == "--top":
            args["top"] = int(next(it))
        elif tok == "--apply":
            args["apply"] = True
        elif tok == "--res":
            args["res"] = int(next(it))
        elif tok == "--recent":
            args["recent"] = int(next(it))
    return args


def _model_name(meta) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", str(meta.get("name", "asset")).lower()).strip("_")


def phase_request(asset_dir: str, top: int, res: int, recent: int = 0) -> None:
    """上位候補を再生成・レンダリングし、レビュー依頼を書き出す。

    recent>0 のときは直近 recent 試行（= 現ラウンド分）だけを対象にする。
    """
    meta = _load_asset_meta(asset_dir)
    G = _load_generator(meta)
    name = _model_name(meta)
    learn_dir = os.path.join(asset_dir, "learn")
    renders_dir = os.path.join(learn_dir, "renders")

    candidates = []
    seen = set()
    with open(os.path.join(learn_dir, "attempts.jsonl"), encoding="utf-8") as f:
        lines = f.readlines()
    if recent > 0:
        lines = lines[-recent:]
    for line in lines:
            a = json.loads(line)
            if a.get("valid"):
                key = json.dumps(a["params"], sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    candidates.append(a)
    candidates.sort(key=lambda a: a["score"], reverse=True)
    candidates = candidates[:top]
    if not candidates:
        print("[visual] 成功した試行がありません。先に optimizer を実行してください。")
        sys.exit(1)

    request = []
    for i, a in enumerate(candidates):
        G.build(a["params"], name=name)
        img = os.path.join(renders_dir, f"cand_{i}.png")
        render_scene(img, res)
        request.append({"id": str(i), "image": os.path.relpath(img),
                        "engine_score": a["score"], "params": a["params"]})
        print(f"[visual] 候補{i}: engine={a['score']} → {img}")

    req_path = os.path.join(learn_dir, "review_request.json")
    with open(req_path, "w", encoding="utf-8") as f:
        json.dump(request, f, ensure_ascii=False, indent=2)
    print(f"[visual] レビュー依頼: {req_path}")
    print("[visual] agents/modeler.md の観点で各画像を 0-10 で採点し、"
          f"{os.path.join(learn_dir, 'review_scores.json')} に保存して --apply を実行")


def phase_apply(asset_dir: str) -> None:
    """視覚スコアをエンジンスコアにブレンドし、知識ベースを再ランクする。"""
    meta = _load_asset_meta(asset_dir)
    G = _load_generator(meta)
    name = _model_name(meta)
    learn_dir = os.path.join(asset_dir, "learn")

    with open(os.path.join(learn_dir, "review_request.json"), encoding="utf-8") as f:
        request = json.load(f)
    with open(os.path.join(learn_dir, "review_scores.json"), encoding="utf-8") as f:
        scores = json.load(f)

    reviewed = []
    for item in request:
        rv = scores.get(item["id"])
        if rv is None:
            continue
        blended = round(item["engine_score"] + VISUAL_WEIGHT * float(rv["visual"]), 2)
        reviewed.append({"params": item["params"], "score": blended,
                         "engine_score": item["engine_score"],
                         "visual": rv["visual"], "notes": rv.get("notes", "")})
        print(f"[visual] 候補{item['id']}: engine={item['engine_score']} "
              f"+ visual={rv['visual']}×{VISUAL_WEIGHT} → blended={blended}")
    if not reviewed:
        print("[visual] review_scores.json に有効なスコアがありません")
        sys.exit(1)

    reviewed.sort(key=lambda a: a["score"], reverse=True)

    # 知識ベースをブレンド済みスコアで再ランク（次回の探索が美的評価を反映する）
    lessons_path = os.path.join(learn_dir, "lessons.json")
    lessons = L.load(lessons_path)
    lessons["top_k"] = [{"params": a["params"], "score": a["score"]}
                        for a in reviewed[:L.TOP_K]]
    keys = reviewed[0]["params"].keys()
    lessons["sweet_spot"] = {
        k: round(sum(a["params"].get(k, 0) for a in lessons["top_k"])
                 / len(lessons["top_k"]), 4) for k in keys}
    best = reviewed[0]
    lessons["best"] = {"params": best["params"], "score": best["score"],
                       "realized": None}
    lessons.setdefault("visual_reviews", []).append(
        [{k: a[k] for k in ("score", "engine_score", "visual", "notes")}
         for a in reviewed])
    L.save(lessons, lessons_path)
    with open(os.path.join(learn_dir, "LESSONS.md"), "w", encoding="utf-8") as f:
        f.write(L.to_markdown(lessons))

    # ブレンド済みベストを保存・レンダリング
    G.build(best["params"], name=name)
    out_blend = os.path.join(asset_dir, "highpoly", "base.blend")
    G.save(out_blend)
    preview = os.path.join(asset_dir, "concept", "preview_visual_best.png")
    G.build(best["params"], name=name)
    render_scene(preview, 600)
    print(f"[visual] ブレンド済みベスト(score={best['score']}, visual={best['visual']}) "
          f"を保存: {out_blend}")
    print(f"[visual] プレビュー: {preview}")


def main():
    import bpy  # noqa: F401

    args = _parse_args(sys.argv)
    assert args["asset"], "--asset を指定してください"
    asset_dir = os.path.abspath(args["asset"])
    if args["apply"]:
        phase_apply(asset_dir)
    else:
        phase_request(asset_dir, args["top"], args["res"], args["recent"])


if __name__ == "__main__":
    main()
