"""Blend 内のメッシュを standards.yaml に照らして検査する Blender スクリプト。

使い方:
    blender --background --python scripts/checks/validate_mesh.py -- \
        --blend assets/characters/my-goblin/lowpoly/lowpoly.blend \
        --type npc_character

合否を標準出力に出し、失敗時は終了コード 1 で抜ける（CI で利用可能）。
検査項目: 命名規則 / スケール / マニフォールド / Ngon / 浮きジオメトリ / UV / ポリゴン予算
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.lib.standards import load_standards  # noqa: E402


def _parse_args(argv: list[str]) -> dict:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    args = {"blend": None, "type": "npc_character"}
    it = iter(argv)
    for tok in it:
        if tok == "--blend":
            args["blend"] = next(it)
        elif tok == "--type":
            args["type"] = next(it)
    return args


def main() -> None:
    import re

    import bmesh
    import bpy

    args = _parse_args(sys.argv)
    std = load_standards()
    failures: list[str] = []

    if args["blend"]:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args["blend"]))

    rules = std["mesh_rules"]
    naming = std["naming"]
    obj_re = re.compile(naming["object_regex"])
    mat_re = re.compile(naming["material_regex"])

    budget = std["poly_budget"].get(args["type"])
    total_tris = 0
    scene_min_z = float("inf")
    scene_max_z = float("-inf")

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        failures.append("メッシュオブジェクトが存在しません")

    for obj in meshes:
        # 命名
        if not obj_re.match(obj.name):
            failures.append(f"命名規則違反 (object): {obj.name}")
        for slot in obj.material_slots:
            if slot.material and not mat_re.match(slot.material.name):
                failures.append(f"命名規則違反 (material): {slot.material.name}")

        # バウンディングからスケール集計
        for corner in obj.bound_box:
            world = obj.matrix_world @ __import__("mathutils").Vector(corner)
            scene_min_z = min(scene_min_z, world.z)
            scene_max_z = max(scene_max_z, world.z)

        # bmesh で詳細検査
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        if rules.get("forbid_ngons"):
            ngons = [f for f in bm.faces if len(f.verts) > 4]
            if ngons:
                failures.append(f"{obj.name}: Ngon {len(ngons)} 面（4角以下にしてください）")

        if rules.get("require_manifold"):
            non_manifold = [e for e in bm.edges if not e.is_manifold]
            if non_manifold:
                failures.append(f"{obj.name}: 非多様体エッジ {len(non_manifold)} 本")

        if rules.get("forbid_loose_geometry"):
            loose_v = [v for v in bm.verts if not v.link_edges]
            loose_e = [e for e in bm.edges if not e.link_faces]
            if loose_v or loose_e:
                failures.append(
                    f"{obj.name}: 浮きジオメトリ（頂点{len(loose_v)} 辺{len(loose_e)}）"
                )

        if rules.get("require_uv") and not obj.data.uv_layers:
            failures.append(f"{obj.name}: UV がありません")

        total_tris += sum(max(0, len(f.verts) - 2) for f in bm.faces)
        bm.free()

    # スケール検査
    units = std["units"]
    if scene_max_z > scene_min_z:
        height = scene_max_z - scene_min_z
        if not (units["character_height_min"] <= height <= units["character_height_max"]):
            failures.append(
                f"スケール異常: 高さ {height:.2f}m "
                f"(許容 {units['character_height_min']}–{units['character_height_max']}m)"
            )

    # ポリゴン予算
    if budget is not None and total_tris > budget:
        failures.append(f"ポリゴン予算超過: {total_tris} > {budget} tris ({args['type']})")

    print(f"[validate] tris={total_tris} type={args['type']} budget={budget}")
    if failures:
        print("[validate] FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("[validate] OK ✅")


if __name__ == "__main__":
    main()
