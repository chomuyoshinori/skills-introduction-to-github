"""web 参照（画像/動画/論文）から得たポーズ・形のヒントを学習に取り込む。

役割分担:
  - web 検索と画像理解は **AI が担当**（agents/reference-scout.md）。AI が
    references/sources.json（出典URL・ライセンス注記）と
    references/reference_hints.json（参照から推定した数値パラメータ＋出典）を書く。
  - 本スクリプトは **検証と適用** を担当（bpy 非依存）。ヒントを生成器の定義域で
    検証・クランプし、learn/reference_target.json として最適化の初期目標に反映する。

著作権への配慮:
  参照画像/動画そのものはリポジトリに保存しない。保存するのは URL・出典・
  ライセンス注記と、そこから導いた数値（測定値＝事実）のみ。

使い方:
  python scripts/learn/reference.py --asset assets/characters/dire-wolf --apply
  python scripts/learn/reference.py --asset assets/characters/dire-wolf --status
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.learn import lessons as L  # noqa: E402
from scripts.learn.optimizer import _load_asset_meta, _load_generator  # noqa: E402


def _paths(asset_dir: str) -> dict:
    return {
        "sources": os.path.join(asset_dir, "references", "sources.json"),
        "hints": os.path.join(asset_dir, "references", "reference_hints.json"),
        "applied": os.path.join(asset_dir, "references", "applied.json"),
        "ref_target": os.path.join(asset_dir, "learn", "reference_target.json"),
        "lessons": os.path.join(asset_dir, "learn", "lessons.json"),
    }


def apply(asset_dir: str) -> None:
    meta = _load_asset_meta(asset_dir)
    G = _load_generator(meta)  # bpy 非依存（PARAM_BOUNDS/clamp_params のみ）
    p = _paths(asset_dir)

    with open(p["hints"], encoding="utf-8") as f:
        hints = json.load(f)
    sources = {}
    if os.path.exists(p["sources"]):
        with open(p["sources"], encoding="utf-8") as f:
            sources = {s["id"]: s for s in json.load(f).get("sources", [])}

    ref_target: dict[str, float] = {}
    provenance: list[dict] = []
    for param, h in hints.get("params", {}).items():
        if param not in G.PARAM_BOUNDS:
            print(f"[reference] 警告: 未知パラメータ '{param}' をスキップ")
            continue
        lo, hi = G.PARAM_BOUNDS[param]
        raw = float(h["value"])
        val = max(lo, min(hi, raw))
        ref_target[param] = val
        cited = [sources.get(sid, {}).get("title", sid) for sid in h.get("from", [])]
        provenance.append({"param": param, "value": val,
                           "clamped": val != raw, "raw": raw,
                           "confidence": h.get("confidence", "?"),
                           "note": h.get("note", ""), "sources": h.get("from", []),
                           "source_titles": cited})

    os.makedirs(os.path.dirname(p["ref_target"]), exist_ok=True)
    with open(p["ref_target"], "w", encoding="utf-8") as f:
        json.dump(ref_target, f, ensure_ascii=False, indent=2)
    with open(p["applied"], "w", encoding="utf-8") as f:
        json.dump({"subject": hints.get("subject", ""), "params": provenance},
                  f, ensure_ascii=False, indent=2)

    # 目標の定義が変わったので、物理的知見(可動域・seg境界)は保持しつつ
    # best/top_k/sweet_spot をリセットし、参照目標で再最適化させる。
    if os.path.exists(p["lessons"]):
        lessons = L.load(p["lessons"])
        lessons["best"] = None
        lessons["top_k"] = []
        lessons["sweet_spot"] = {}
        L.save(lessons, p["lessons"])

    print(f"=== 参照を適用: {hints.get('subject', '')} ===")
    for pr in provenance:
        clam = " (定義域にクランプ)" if pr["clamped"] else ""
        src = ", ".join(pr["source_titles"]) or "(出典未記載)"
        print(f"  {pr['param']:>20} = {pr['value']:<7} [{pr['confidence']}]{clam}")
        print(f"  {'':>20}   ← {pr['note']}  出典: {src}")
    print(f"[reference] reference_target.json を書き出し: 次の optimizer 実行で初期目標に反映")


def status(asset_dir: str) -> None:
    p = _paths(asset_dir)
    if not os.path.exists(p["applied"]):
        print("[reference] まだ参照を適用していません。--apply を実行してください。")
        return
    with open(p["applied"], encoding="utf-8") as f:
        applied = json.load(f)
    print(f"参照対象: {applied.get('subject', '')}")
    print("パラメータ | 値 | 信頼度 | 出典")
    for pr in applied["params"]:
        src = ", ".join(pr.get("source_titles", [])) or "(未記載)"
        print(f"  {pr['param']:>20} | {pr['value']:<7} | {pr['confidence']:<6} | {src}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true", help="reference_hints.json を検証・適用")
    g.add_argument("--status", action="store_true", help="適用済み参照を表示")
    args = ap.parse_args()
    asset_dir = os.path.abspath(args.asset)
    if args.apply:
        apply(asset_dir)
    else:
        status(asset_dir)


if __name__ == "__main__":
    main()
