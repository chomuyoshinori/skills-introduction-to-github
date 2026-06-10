"""現在の Blender シーン上のメッシュを standards.yaml に照らして検査するコア。

validate_mesh.py（CLI）と学習ループ（scripts/learn/）の両方から再利用する。
bpy が import 済みの前提で呼ぶこと。
"""
from __future__ import annotations

import re
from typing import Any


def validate_scene_meshes(std: dict[str, Any], asset_type: str) -> dict[str, Any]:
    """シーン内の全メッシュを検査し、結果 dict を返す。

    返り値:
        {
          "ok": bool,
          "failures": list[str],
          "fail_kinds": set[str],   # 'naming'|'scale'|'ngon'|'manifold'|'loose'|'uv'|'budget'|'empty'
          "tris": int,
          "height": float,
        }
    """
    import bmesh
    import bpy
    import mathutils

    rules = std["mesh_rules"]
    naming = std["naming"]
    obj_re = re.compile(naming["object_regex"])
    mat_re = re.compile(naming["material_regex"])
    units = std["units"]
    budget = std["poly_budget"].get(asset_type)

    failures: list[str] = []
    fail_kinds: set[str] = set()
    total_tris = 0
    min_z, max_z = float("inf"), float("-inf")

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        failures.append("メッシュオブジェクトが存在しません")
        fail_kinds.add("empty")

    for obj in meshes:
        if not obj_re.match(obj.name):
            failures.append(f"命名規則違反 (object): {obj.name}")
            fail_kinds.add("naming")
        for slot in obj.material_slots:
            if slot.material and not mat_re.match(slot.material.name):
                failures.append(f"命名規則違反 (material): {slot.material.name}")
                fail_kinds.add("naming")

        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            min_z = min(min_z, world.z)
            max_z = max(max_z, world.z)

        bm = bmesh.new()
        bm.from_mesh(obj.data)

        if rules.get("forbid_ngons"):
            ngons = [f for f in bm.faces if len(f.verts) > 4]
            if ngons:
                failures.append(f"{obj.name}: Ngon {len(ngons)} 面")
                fail_kinds.add("ngon")

        if rules.get("require_manifold"):
            non_manifold = [e for e in bm.edges if not e.is_manifold]
            if non_manifold:
                failures.append(f"{obj.name}: 非多様体エッジ {len(non_manifold)} 本")
                fail_kinds.add("manifold")

        if rules.get("forbid_loose_geometry"):
            loose_v = [v for v in bm.verts if not v.link_edges]
            loose_e = [e for e in bm.edges if not e.link_faces]
            if loose_v or loose_e:
                failures.append(
                    f"{obj.name}: 浮きジオメトリ（頂点{len(loose_v)} 辺{len(loose_e)}）"
                )
                fail_kinds.add("loose")

        if rules.get("require_uv") and not obj.data.uv_layers:
            failures.append(f"{obj.name}: UV がありません")
            fail_kinds.add("uv")

        total_tris += sum(max(0, len(f.verts) - 2) for f in bm.faces)
        bm.free()

    height = (max_z - min_z) if max_z > min_z else 0.0
    if height > 0 and not (
        units["character_height_min"] <= height <= units["character_height_max"]
    ):
        failures.append(
            f"スケール異常: 高さ {height:.2f}m "
            f"(許容 {units['character_height_min']}–{units['character_height_max']}m)"
        )
        fail_kinds.add("scale")

    if budget is not None and total_tris > budget:
        failures.append(f"ポリゴン予算超過: {total_tris} > {budget} tris ({asset_type})")
        fail_kinds.add("budget")

    return {
        "ok": not failures,
        "failures": failures,
        "fail_kinds": fail_kinds,
        "tris": total_tris,
        "height": height,
    }
