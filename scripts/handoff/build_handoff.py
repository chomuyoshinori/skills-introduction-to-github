"""合格したブロッキングを仕上げ工程へ引き継ぐパッケージを生成する。

スカルプト（毛・指・表情）は創造的判断なので自動化しない。代わりに、次の担当
（人＋agents/modeler.md, texture-artist.md）が即作業を始められる資料一式を作る:

  highpoly/turnaround_*.png   前/右/背/左の4方向レンダリング
  export/<name>.glb           検証済みの最終ブロッキング
  HANDOFF.md                  仕様・学習履歴・スカルプト指示書

文書生成(build_handoff_doc)は bpy 非依存でテスト可能。レンダリング/書き出しは
bpy が要る部分だけ分離してある。

使い方:
  blender --background --python scripts/handoff/build_handoff.py -- \
      --asset assets/characters/dire-wolf
  # 文書のみ（bpy 不要・CI 可）:
  python scripts/handoff/build_handoff.py --asset assets/characters/dire-wolf --doc-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.learn.optimizer import _load_asset_meta  # noqa: E402
from scripts.lib.standards import load_standards  # noqa: E402

TURNAROUND = [("front", 0), ("right", 90), ("back", 180), ("left", 270)]


def _final_target(asset_dir: str, meta: dict) -> dict:
    target = dict(meta.get("target") or {})
    for fn in ("reference_target.json", "working_target.json"):
        p = os.path.join(asset_dir, "learn", fn)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                target.update(json.load(f))
    return target


def _critique_summary(asset_dir: str) -> list[dict]:
    p = os.path.join(asset_dir, "learn", "critique_history.jsonl")
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out.append({"round": r["round"], "overall": r["overall"],
                        "passed": r["passed"], "summary": r.get("summary", "")})
    return out


def build_handoff_doc(asset_dir: str) -> str:
    """引き継ぎ文書(HANDOFF.md)の本文を組み立てて返す（bpy 非依存）。"""
    meta = _load_asset_meta(asset_dir)
    std = load_standards()
    atype = meta.get("type", "npc_character")
    budget = std["poly_budget"].get(atype)
    target = _final_target(asset_dir, meta)
    history = _critique_summary(asset_dir)
    name = meta.get("display_name") or meta.get("name", "asset")

    refs_path = os.path.join(asset_dir, "references", "sources.json")
    refs = []
    if os.path.exists(refs_path):
        with open(refs_path, encoding="utf-8") as f:
            refs = json.load(f).get("sources", [])

    lines: list[str] = []
    lines.append(f"# 引き継ぎ: {name}")
    lines.append("")
    lines.append("> このファイルは scripts/handoff/build_handoff.py が自動生成します。")
    lines.append("> ブロッキングは検証・合格済みです。ここから先の造形は人＋専門エージェントが担当します。")
    lines.append("")
    lines.append("## 成果物")
    lines.append("- `export/` … 検証済みの最終ブロッキング（glb）")
    lines.append("- `highpoly/base.blend` … リグ(ROM制約)付きの .blend")
    lines.append("- `highpoly/turnaround_{front,right,back,left}.png` … 4方向ビュー")
    lines.append("")

    lines.append("## 仕様（達成済みプロポーション/ポーズ）")
    lines.append(f"- 種別: `{atype}` / ポリゴン予算: {budget} tris")
    if target:
        lines.append("- 目標値（参照接地＋critic調整の最終形）:")
        for k, v in target.items():
            shown = round(v, 3) if isinstance(v, float) else v
            lines.append(f"  - {k}: {shown}")
    lines.append("")

    if history:
        passed = next((h for h in history if h["passed"]), None)
        lines.append("## 品質の達成経緯")
        if passed:
            lines.append(f"- **合格: ラウンド {passed['round']} / スコア {passed['overall']}**")
        lines.append(f"- 反復ラウンド数: {len(history)}")
        lines.append("- スコア推移: " + " → ".join(str(h["overall"]) for h in history))
        if passed:
            lines.append("")
            lines.append("批評家の最終評価:")
            lines.append(f"> {passed['summary']}")
        lines.append("")

    lines.append("## スカルプト指示書（次の担当へ）")
    lines.append("ブロッキングはプロポーションとポーズの土台です。次の工程で作り込んでください:")
    lines.append("")
    lines.append("1. **リトポ前のディテール（highpoly）**")
    lines.append("   - 関節球は造形の当たり。実際の筋・腱の流れに沿って繋ぐ")
    lines.append("   - シルエットを壊さない範囲で面取り・肉付け")
    lines.append("2. **造形の要点**（critic が重視した点を引き継ぐ）")
    for hint in _sculpt_hints(meta):
        lines.append(f"   - {hint}")
    lines.append("3. **リグ**: `base.blend` のボーンには可動域(Limit Rotation)が焼き込み済み。"
                 "これを尊重したウェイト付けを行う（`config/anatomy.yaml` 参照）")
    lines.append("4. **検査**: 仕上げ後も `scripts/checks/validate_mesh.py` を通すこと")
    lines.append("")
    lines.append("担当エージェント: `agents/modeler.md`（造形レビュー）/ "
                 "`agents/retopo-uv.md`（リトポ）/ `agents/texture-artist.md`（質感）")
    lines.append("")

    if refs:
        lines.append("## 参照（出典のみ・メディアは未保存）")
        for s in refs:
            lines.append(f"- [{s.get('title', s.get('id'))}]({s.get('url', '')})"
                         f" — {s.get('license_note', '')}")
        lines.append("")

    return "\n".join(lines) + "\n"


def _sculpt_hints(meta: dict) -> list[str]:
    """種別・generator に応じた造形の要点。"""
    if meta.get("generator") == "quadruped":
        return [
            "頭部: 立ち耳の薄さと吻の長さがイヌ科の生命線。丸めすぎない",
            "胴: 深い胸と絞れた腰のラインを強調し、肋骨の張りを出す",
            "四肢: 後肢の stifle/hock の二段の折れを筋肉で繋ぎ、肉球で接地",
            "尾: 付け根を太く先を房状に。毛流れで動きを出す",
        ]
    return [
        "頭部: 大きめの頭のキャラ性を活かしつつ、顔のディテールを作る",
        "胴: 量感（嵩）を保ったまま筋肉のメリハリを付ける",
        "四肢: 関節球を当たりに、肘・膝の方向を明確に",
        "手足: ブロッキングには無い指を追加する",
    ]


def _render_and_export(asset_dir: str) -> None:
    """bpy が要る部分: turnaround レンダリングと glb 書き出し。"""
    import re

    from scripts.lib.blendio import open_blend
    from scripts.lib.viz import render_scene
    from scripts.learn.optimizer import _load_generator

    meta = _load_asset_meta(asset_dir)
    std = load_standards()
    blend = os.path.join(asset_dir, "highpoly", "base.blend")

    for label, az in TURNAROUND:
        open_blend(blend)
        out = os.path.join(asset_dir, "highpoly", f"turnaround_{label}.png")
        render_scene(out, 600, azimuth_deg=az)
        print(f"[handoff] turnaround: {out}")

    name = re.sub(r"[^a-z0-9]+", "_", str(meta.get("name", "asset")).lower()).strip("_")
    exp = std.get("export", {})
    open_blend(blend)
    import bpy

    out_glb = os.path.join(asset_dir, "export", f"{name}.glb")
    os.makedirs(os.path.dirname(out_glb), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(out_glb), export_format="GLB",
                              export_apply=bool(exp.get("apply_modifiers", True)))
    print(f"[handoff] glb: {out_glb}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True)
    ap.add_argument("--doc-only", action="store_true",
                    help="bpy を使わず HANDOFF.md のみ生成")
    args = _parse(ap)
    asset_dir = os.path.abspath(args.asset)

    if not args.doc_only:
        _render_and_export(asset_dir)

    doc = build_handoff_doc(asset_dir)
    out = os.path.join(asset_dir, "HANDOFF.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"[handoff] 引き継ぎ文書: {out}")


def _parse(ap):
    # blender 経由では "--" 以降が引数。素の python ではそのまま。
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]
    return ap.parse_args(argv)


if __name__ == "__main__":
    main()
