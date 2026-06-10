"""パラメトリックなヒューマノイド・ブロッキング生成器。

球(関節)＋円柱(手足/胴)で人体を組み、1つのメッシュに統合する。
円柱のフタは TRIFAN にして Ngon を避け、各パーツは閉じた多様体メッシュなので
standards.yaml の検査を通る。学習ループ(scripts/learn/)がパラメータを探索する対象。

bpy が利用可能な環境でのみ動作する。
"""
from __future__ import annotations

from typing import Any

# 探索対象パラメータの定義域（min, max）。学習ループはこの範囲で探索する。
# height と seg はわざと検査限界をまたぐ広さにしてある。
# こうすることで「スケール検査落ち」「ポリゴン予算超過」という実際の失敗が起き、
# 学習ループがそこから制約を学べる（成功も失敗も学習対象にする狙い）。
PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "height_m": (0.2, 3.5),      # 全体の高さ(m)。0.3未満/3.0超はスケール検査に落ちる
    "head_ratio": (0.14, 0.30),  # 頭の高さ / 全高
    "torso_ratio": (0.28, 0.42),
    "leg_ratio": (0.34, 0.50),
    "arm_ratio": (0.30, 0.46),   # 腕の長さ / 全高
    "shoulder_w": (0.12, 0.30),  # 肩幅の半分(m)
    "limb_radius": (0.04, 0.11), # 手足の半径(m)
    "lean_deg": (0.0, 25.0),     # 前傾角(度)
    "seg": (6, 200),             # メッシュ解像度。高すぎるとポリゴン予算を超過する
}


def clamp_params(p: dict[str, float]) -> dict[str, float]:
    """パラメータを定義域に収める。seg は整数に丸める。"""
    out = dict(p)
    for k, (lo, hi) in PARAM_BOUNDS.items():
        if k in out:
            out[k] = max(lo, min(hi, out[k]))
    out["seg"] = int(round(out.get("seg", 12)))
    return out


def default_params() -> dict[str, float]:
    """各範囲の中央値を初期値とする。"""
    return clamp_params({k: (lo + hi) / 2 for k, (lo, hi) in PARAM_BOUNDS.items()})


def build_humanoid(params: dict[str, float], name: str = "goblin") -> dict[str, Any]:
    """params からヒューマノイドを生成し、実現メトリクスを返す。

    返り値: {"realized": {...}, "object_name": str}
    """
    import bpy
    import mathutils

    p = clamp_params(params)
    H = p["height_m"]
    seg = max(3, p["seg"])
    r = p["limb_radius"]

    leg_len = p["leg_ratio"] * H
    torso_len = p["torso_ratio"] * H
    head_d = p["head_ratio"] * H          # 頭の直径
    arm_len = p["arm_ratio"] * H
    shoulder = p["shoulder_w"]
    lean = mathutils.Matrix.Rotation(__import__("math").radians(p["lean_deg"]), 4, "X")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    parts: list[Any] = []

    def cylinder(x, z0, z1, radius):
        mid = (z0 + z1) / 2
        depth = abs(z1 - z0)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=seg, radius=radius, depth=depth,
            end_fill_type="TRIFAN", location=(x, 0, mid),
        )
        parts.append(bpy.context.active_object)

    def sphere(x, z, radius, pivot=None):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=seg, ring_count=max(3, seg // 2), radius=radius, location=(x, 0, z),
        )
        obj = bpy.context.active_object
        if pivot is not None:
            _rotate_about(obj, lean, pivot)
        parts.append(obj)

    hip_z = leg_len
    pivot = mathutils.Vector((0, 0, hip_z))

    # 脚（2本）
    cylinder(-shoulder * 0.5, 0.0, leg_len, r)
    cylinder(shoulder * 0.5, 0.0, leg_len, r)

    # 胴（前傾を反映）
    cylinder(0.0, hip_z, hip_z + torso_len, r * 1.6)
    _rotate_about(parts[-1], lean, pivot)
    shoulder_z = hip_z + torso_len

    # 頭（前傾の延長線上）
    head_center = pivot + lean.to_3x3() @ mathutils.Vector((0, 0, torso_len + head_d / 2))
    sphere(head_center.x, head_center.z, head_d / 2)
    _set_y(parts[-1], head_center.y)

    # 腕（2本、肩から下げる）
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=seg, radius=r * 0.8, depth=arm_len, end_fill_type="TRIFAN",
            location=(sx * shoulder, 0, shoulder_z - arm_len / 2),
        )
        arm = bpy.context.active_object
        _rotate_about(arm, lean, pivot)
        parts.append(arm)

    # 統合
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = f"CHR_{name}_base_LOD0"

    # マテリアル（命名規則 MAT_*）
    mat = bpy.data.materials.new(f"MAT_{name}_base")
    body.data.materials.append(mat)

    # UV（円柱/球は既定UVを持つが、統合で欠ける場合に備えスマートUV）
    if not body.data.uv_layers:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode="OBJECT")

    # 実現メトリクス
    min_z = min((body.matrix_world @ mathutils.Vector(c)).z for c in body.bound_box)
    max_z = max((body.matrix_world @ mathutils.Vector(c)).z for c in body.bound_box)
    realized_h = max_z - min_z
    tris = sum(max(0, len(poly.vertices) - 2) for poly in body.data.polygons)

    realized = {
        "height_m": realized_h,
        "head_ratio": head_d / realized_h if realized_h else 0,
        "torso_ratio": torso_len / realized_h if realized_h else 0,
        "leg_ratio": leg_len / realized_h if realized_h else 0,
        "arm_ratio": arm_len / realized_h if realized_h else 0,
        "shoulder_w": shoulder,
        "lean_deg": p["lean_deg"],
        "tris": tris,
    }
    return {"realized": realized, "object_name": body.name}


def save(path: str) -> None:
    import bpy

    import os

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path))


def _rotate_about(obj, rot_mat, pivot):
    import mathutils

    loc = obj.location.copy()
    obj.location = pivot + rot_mat.to_3x3() @ (loc - pivot)
    obj.rotation_euler = (rot_mat @ obj.matrix_world).to_euler()


def _set_y(obj, y):
    obj.location.y = y
