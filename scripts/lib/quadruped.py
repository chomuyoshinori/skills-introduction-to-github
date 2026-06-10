"""パラメトリックな四足動物（イヌ科）生成器。

イヌ科の骨格構造を反映する:
- 後肢は 大腿 → stifle(膝) → 下腿 → hock(飛節) → 中足 の3節。
  stifle は常に屈曲位（伸びきらない）、hock は逆向きに曲がって見える。
- 前肢は 上腕 → elbow → 前腕 の2節。
関節位置は運動学で計算し、接地するよう体高を決める。
リグには config/anatomy.yaml (quadruped_canine) の可動域を焼き込む。

humanoid.py と同じインターフェース（PARAM_BOUNDS / clamp_params / build / save）
を持ち、学習ループから差し替え可能。bpy 必須。
"""
from __future__ import annotations

import math
from typing import Any

# 探索対象パラメータの定義域。ポーズ角は可動域(anatomy.yaml)を
# わざと超える広さにし、学習ループが違反から可動域を学べるようにする。
PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "body_length_m": (0.3, 2.2),     # 体幹長（胸〜骨盤）
    "head_ratio": (0.15, 0.35),      # 頭の直径 / 体幹長
    "neck_ratio": (0.15, 0.40),      # 首の長さ / 体幹長
    "hind_leg_ratio": (0.35, 0.75),  # 後肢全長 / 体幹長
    "front_leg_ratio": (0.35, 0.75),
    "body_radius_ratio": (0.10, 0.22),
    "tail_ratio": (0.20, 0.60),
    "limb_radius": (0.025, 0.08),
    "seg": (6, 200),
    # ポーズ角（度）。ROM: 首-20..30 / 股-30..110 / stifle20..130 / hock30..140
    #                  / 肩-40..160 / 肘20..150
    "neck_pitch_deg": (-40, 50),
    "hip_pitch_deg": (-50, 140),
    "stifle_deg": (-10, 170),
    "hock_deg": (0, 180),
    "shoulder_pitch_deg": (-70, 190),
    "elbow_deg": (-10, 180),
}

POSE_KEYS = ("neck_pitch_deg", "hip_pitch_deg", "stifle_deg", "hock_deg",
             "shoulder_pitch_deg", "elbow_deg")


def clamp_params(p: dict[str, float]) -> dict[str, float]:
    out = dict(p)
    for k, (lo, hi) in PARAM_BOUNDS.items():
        if k in out:
            out[k] = max(lo, min(hi, out[k]))
    out["seg"] = int(round(out.get("seg", 12)))
    return out


def default_params() -> dict[str, float]:
    return clamp_params({k: (lo + hi) / 2 for k, (lo, hi) in PARAM_BOUNDS.items()})


def build(params: dict[str, float], name: str = "wolf",
          with_rig: bool = True) -> dict[str, Any]:
    """params から四足動物を生成し、実現メトリクスを返す。前方は -Y。"""
    import bpy
    import mathutils

    V = mathutils.Vector
    p = clamp_params(params)
    L = p["body_length_m"]
    seg = max(3, p["seg"])
    r = p["limb_radius"]
    body_r = p["body_radius_ratio"] * L
    head_d = p["head_ratio"] * L
    neck_len = p["neck_ratio"] * L
    hind_len = p["hind_leg_ratio"] * L
    front_len = p["front_leg_ratio"] * L
    tail_len = p["tail_ratio"] * L

    # 後肢3節 / 前肢2節の配分
    thigh_len, shank_len, meta_len = hind_len * 0.40, hind_len * 0.35, hind_len * 0.25
    upper_len, fore_len = front_len * 0.45, front_len * 0.55

    hip_pitch = math.radians(p["hip_pitch_deg"])
    stifle = math.radians(p["stifle_deg"])
    hock = math.radians(p["hock_deg"])
    sh_pitch = math.radians(p["shoulder_pitch_deg"])
    elbow = math.radians(p["elbow_deg"])
    neck_elev = math.radians(25 + p["neck_pitch_deg"])  # 水平からの首の仰角

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    parts: list[Any] = []

    def dir_down(a: float) -> Any:
        """真下からの前方ピッチ a（+で前方 = -Y）の単位ベクトル。"""
        return V((0, -math.sin(a), -math.cos(a)))

    def cylinder_between(p1, p2, radius):
        v = p2 - p1
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=seg, radius=radius, depth=max(v.length, 1e-4),
            end_fill_type="TRIFAN", location=(0, 0, 0),
        )
        obj = bpy.context.active_object
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = v.to_track_quat("Z", "Y")
        obj.location = (p1 + p2) / 2
        parts.append(obj)

    def sphere(center, radius):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=seg, ring_count=max(3, seg // 2),
            radius=radius, location=center,
        )
        parts.append(bpy.context.active_object)

    # --- 運動学: 接地するように体高を決める ---
    # 後肢: 大腿(前方+) → stifle屈曲で下腿は後方へ → hock屈曲で中足は前方へ戻る
    a_thigh = hip_pitch
    a_shank = a_thigh - stifle
    a_meta = a_shank + hock
    hind_drop = (thigh_len * math.cos(a_thigh) + shank_len * math.cos(a_shank)
                 + meta_len * math.cos(a_meta))
    hip_h = max(hind_drop + r, 2 * r)

    # 前肢: 上腕(通常は後方=負) → 肘屈曲で前腕は前方へ
    a_upper = sh_pitch
    a_fore = a_upper + elbow
    front_drop = upper_len * math.cos(a_upper) + fore_len * math.cos(a_fore)
    shoulder_h = max(front_drop + r, 2 * r)

    pelvis = V((0, L / 2, hip_h))
    chest = V((0, -L / 2, shoulder_h))
    leg_x = body_r * 0.8

    joints: dict[str, Any] = {"pelvis": pelvis, "chest": chest}
    for side, sgn in (("L", 1), ("R", -1)):
        hip = pelvis + V((sgn * leg_x, 0, 0))
        stifle_j = hip + thigh_len * dir_down(a_thigh)
        hock_j = stifle_j + shank_len * dir_down(a_shank)
        paw_h = hock_j + meta_len * dir_down(a_meta)
        joints[f"hip.{side}"] = hip
        joints[f"stifle.{side}"] = stifle_j
        joints[f"hock.{side}"] = hock_j
        joints[f"hindpaw.{side}"] = paw_h

        sh = chest + V((sgn * leg_x, 0, 0))
        elbow_j = sh + upper_len * dir_down(a_upper)
        paw_f = elbow_j + fore_len * dir_down(a_fore)
        joints[f"shoulder.{side}"] = sh
        joints[f"elbow.{side}"] = elbow_j
        joints[f"frontpaw.{side}"] = paw_f

    # 首・頭・尾
    neck_dir = V((0, -math.cos(neck_elev), math.sin(neck_elev)))
    neck_end = chest + neck_len * neck_dir
    head_center = neck_end + neck_dir * head_d * 0.3
    snout_end = head_center + V((0, -head_d * 0.8, -head_d * 0.1))
    tail_dir = V((0, math.cos(math.radians(40)), math.sin(math.radians(40))))
    tail_end = pelvis + tail_len * tail_dir
    joints["neck_end"] = neck_end
    joints["tail_end"] = tail_end

    # --- メッシュ生成 ---
    cylinder_between(pelvis, chest, body_r)            # 体幹
    sphere(pelvis, body_r * 1.05)
    sphere(chest, body_r * 1.05)
    cylinder_between(chest, neck_end, body_r * 0.55)   # 首
    sphere(head_center, head_d / 2)                    # 頭
    cylinder_between(head_center, snout_end, head_d * 0.22)  # 鼻先
    cylinder_between(pelvis, tail_end, r * 0.6)        # 尾
    for side in ("L", "R"):
        cylinder_between(joints[f"hip.{side}"], joints[f"stifle.{side}"], r)
        cylinder_between(joints[f"stifle.{side}"], joints[f"hock.{side}"], r * 0.85)
        cylinder_between(joints[f"hock.{side}"], joints[f"hindpaw.{side}"], r * 0.7)
        cylinder_between(joints[f"shoulder.{side}"], joints[f"elbow.{side}"], r * 0.9)
        cylinder_between(joints[f"elbow.{side}"], joints[f"frontpaw.{side}"], r * 0.7)
        sphere(joints[f"hip.{side}"], r * 1.2)
        sphere(joints[f"stifle.{side}"], r * 1.0)
        sphere(joints[f"hock.{side}"], r * 0.9)
        sphere(joints[f"shoulder.{side}"], r * 1.2)
        sphere(joints[f"elbow.{side}"], r * 1.0)
        sphere(joints[f"hindpaw.{side}"], r * 0.9)
        sphere(joints[f"frontpaw.{side}"], r * 0.9)

    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = f"CHR_{name}_base_LOD0"

    mat = bpy.data.materials.new(f"MAT_{name}_base")
    body.data.materials.append(mat)

    if not body.data.uv_layers:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode="OBJECT")

    if with_rig:
        _build_armature(joints, name)

    min_z = min((body.matrix_world @ V(c)).z for c in body.bound_box)
    max_z = max((body.matrix_world @ V(c)).z for c in body.bound_box)
    realized_h = max_z - min_z
    tris = sum(max(0, len(poly.vertices) - 2) for poly in body.data.polygons)

    realized = {
        "height_m": realized_h,
        "body_length_m": L,
        "head_ratio": p["head_ratio"],
        "neck_ratio": p["neck_ratio"],
        "hind_leg_ratio": p["hind_leg_ratio"],
        "front_leg_ratio": p["front_leg_ratio"],
        "tail_ratio": p["tail_ratio"],
        "tris": tris,
    }
    for k in POSE_KEYS:
        realized[k] = p[k]
    return {"realized": realized, "object_name": body.name, "joints": joints}


def _build_armature(joints: dict[str, Any], name: str) -> None:
    """イヌ科の可動域を Limit Rotation 制約としてボーンに焼き込む。"""
    import bpy

    from scripts.lib.anatomy import load_anatomy

    anatomy = load_anatomy().get("quadruped_canine", {}).get("joints", {})

    arm_data = bpy.data.armatures.new(f"RIG_{name}")
    arm_obj = bpy.data.objects.new(f"RIG_{name}", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    def bone(bname, head, tail, parent=None):
        b = arm_data.edit_bones.new(bname)
        b.head, b.tail = head, tail
        if parent:
            b.parent = arm_data.edit_bones[parent]
        return b

    bone("spine", joints["pelvis"], joints["chest"])
    bone("neck", joints["chest"], joints["neck_end"], "spine")
    bone("tail", joints["pelvis"], joints["tail_end"], "spine")
    for s in ("L", "R"):
        bone(f"thigh.{s}", joints[f"hip.{s}"], joints[f"stifle.{s}"], "spine")
        bone(f"shin.{s}", joints[f"stifle.{s}"], joints[f"hock.{s}"], f"thigh.{s}")
        bone(f"foot.{s}", joints[f"hock.{s}"], joints[f"hindpaw.{s}"], f"shin.{s}")
        bone(f"upper_arm.{s}", joints[f"shoulder.{s}"], joints[f"elbow.{s}"], "spine")
        bone(f"forearm.{s}", joints[f"elbow.{s}"], joints[f"frontpaw.{s}"], f"upper_arm.{s}")

    bpy.ops.object.mode_set(mode="POSE")
    bone_joint = {"spine": "spine_pitch", "neck": "spine_pitch",
                  "thigh": "hip_pitch", "shin": "stifle", "foot": "hock",
                  "upper_arm": "shoulder_pitch", "forearm": "elbow"}
    for pb in arm_obj.pose.bones:
        joint = bone_joint.get(pb.name.split(".")[0])
        if joint and joint in anatomy:
            c = pb.constraints.new("LIMIT_ROTATION")
            c.use_limit_x = True
            c.min_x = math.radians(anatomy[joint]["min_deg"])
            c.max_x = math.radians(anatomy[joint]["max_deg"])
            c.owner_space = "LOCAL"
    bpy.ops.object.mode_set(mode="OBJECT")


def save(path: str) -> None:
    import os

    import bpy

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path))
