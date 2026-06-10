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
    # 尾の角度（水平から、+で上向き/-で垂れ下がり）。critic R3 の指摘で追加
    "tail_pitch_deg": (-60, 60),
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


def predict_metrics(params: dict[str, float]) -> dict[str, Any]:
    """params から実現メトリクスを解析的に計算する（bpy 非依存・高速）。

    build() が返す realized dict と一致させる。探索ループはこれで評価し、
    実メッシュ生成は候補/最終確定時のみ bpy で行う（スピード最適化）。
    """
    p = clamp_params(params)
    L = p["body_length_m"]
    r = p["limb_radius"]
    body_r = p["body_radius_ratio"] * L
    head_d = p["head_ratio"] * L
    neck_len = p["neck_ratio"] * L
    hind_len = p["hind_leg_ratio"] * L
    front_len = p["front_leg_ratio"] * L
    thigh_len, shank_len, meta_len = hind_len * 0.40, hind_len * 0.35, hind_len * 0.25
    upper_len, fore_len = front_len * 0.45, front_len * 0.55

    hip_pitch = math.radians(p["hip_pitch_deg"])
    stifle = math.radians(p["stifle_deg"])
    hock = math.radians(p["hock_deg"])
    sh_pitch = math.radians(p["shoulder_pitch_deg"])
    elbow = math.radians(p["elbow_deg"])
    neck_elev = math.radians(25 + p["neck_pitch_deg"])

    a_thigh, a_shank = hip_pitch, hip_pitch - stifle
    a_meta = a_shank + hock
    hind_drop = (thigh_len * math.cos(a_thigh) + shank_len * math.cos(a_shank)
                 + meta_len * math.cos(a_meta))
    hip_h = max(hind_drop + r, 2 * r)
    a_upper, a_fore = sh_pitch, sh_pitch + elbow
    front_drop = upper_len * math.cos(a_upper) + fore_len * math.cos(a_fore)
    shoulder_h = max(front_drop + r, 2 * r)

    # 後肢の踏み込み（hindpaw.y - hip.y）/ L。dir_down(a).y = -sin(a)
    hind_reach_ratio = -(thigh_len * math.sin(a_thigh) + shank_len * math.sin(a_shank)
                         + meta_len * math.sin(a_meta)) / L
    # 前肢の踏み込み（frontpaw.y - shoulder.y）/ L。0=肩の真下に接地（垂直な支柱）
    front_reach_ratio = -(upper_len * math.sin(a_upper) + fore_len * math.sin(a_fore)) / L
    back_slope_deg = math.degrees(math.atan2(hip_h - shoulder_h, L))

    # 首・頭の高さから全高を概算（接地=0）
    neck_end_z = shoulder_h + neck_len * math.sin(neck_elev)
    head_center_z = neck_end_z + head_d * 0.3 * math.sin(neck_elev)
    realized_h = max(head_center_z + head_d / 2, shoulder_h + body_r * 1.18, hip_h + body_r)

    seg = max(3, p["seg"])
    # tris を実メッシュと厳密一致で算出（15球＋14円柱＋2耳コーン＋4立方体。実測フィット済み）
    R = max(3, seg // 2)
    tris = 15 * 2 * seg * (R - 1) + 56 * seg + 4 * (seg // 2) + 48

    realized = {
        "height_m": realized_h,
        "body_length_m": L,
        "head_ratio": p["head_ratio"],
        "neck_ratio": p["neck_ratio"],
        "hind_leg_ratio": p["hind_leg_ratio"],
        "front_leg_ratio": p["front_leg_ratio"],
        "tail_ratio": p["tail_ratio"],
        "body_radius_ratio": p["body_radius_ratio"],
        "tail_pitch_deg": p.get("tail_pitch_deg", 40),
        "back_slope_deg": round(back_slope_deg, 2),
        "shoulder_height_m": round(shoulder_h, 3),
        "hind_reach_ratio": round(hind_reach_ratio, 3),
        "front_reach_ratio": round(front_reach_ratio, 3),
        "limb_radius": r,
        "tris": tris,
    }
    for k in POSE_KEYS:
        realized[k] = p[k]
    return realized


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
    tail_pitch = math.radians(p.get("tail_pitch_deg", 40))
    tail_dir = V((0, math.cos(tail_pitch), math.sin(tail_pitch)))
    tail_end = pelvis + tail_len * tail_dir
    joints["neck_end"] = neck_end
    joints["tail_end"] = tail_end

    # --- メッシュ生成 ---
    cylinder_between(pelvis, chest, body_r * 0.92)     # 体幹
    sphere(pelvis, body_r * 0.92)                       # 腰は絞る
    sphere(chest, body_r * 1.18)                        # 胸郭は深く
    cylinder_between(chest, neck_end, body_r * 0.55)   # 首
    sphere(head_center, head_d / 2)                    # 頭
    # 吻(マズル): 長めに伸ばし先端に鼻の球。オオカミの長い顔を作る
    cylinder_between(head_center, snout_end, head_d * 0.20)
    sphere(snout_end, head_d * 0.16)
    # 耳: 頭頂に2本のコーン（イヌ科の最重要シルエット要素）
    def ear(sx):
        bpy.ops.mesh.primitive_cone_add(
            vertices=max(3, seg // 2), radius1=head_d * 0.17, depth=head_d * 0.50,
            end_fill_type="TRIFAN",
            location=head_center + V((sx * head_d * 0.24, head_d * 0.10, head_d * 0.46)),
        )
        obj = bpy.context.active_object
        obj.rotation_euler = (math.radians(-12), 0, 0)  # わずかに前傾
        parts.append(obj)
    ear(1)
    ear(-1)
    # 尾: 先細り＋先端の房
    cylinder_between(pelvis, tail_end, r * 0.55)
    sphere(tail_end, r * 0.7)
    for side in ("L", "R"):
        cylinder_between(joints[f"hip.{side}"], joints[f"stifle.{side}"], r * 1.25)
        cylinder_between(joints[f"stifle.{side}"], joints[f"hock.{side}"], r * 0.85)
        cylinder_between(joints[f"hock.{side}"], joints[f"hindpaw.{side}"], r * 0.7)
        cylinder_between(joints[f"shoulder.{side}"], joints[f"elbow.{side}"], r * 1.1)
        cylinder_between(joints[f"elbow.{side}"], joints[f"frontpaw.{side}"], r * 0.7)
        sphere(joints[f"hip.{side}"], r * 1.2)
        sphere(joints[f"stifle.{side}"], r * 1.0)
        sphere(joints[f"hock.{side}"], r * 0.9)
        sphere(joints[f"shoulder.{side}"], r * 1.2)
        sphere(joints[f"elbow.{side}"], r * 1.0)
        # 肉球(toe): 各脚の先端から前方へ伸びる箱。指行性の接地を表現
        for paw in (f"hindpaw.{side}", f"frontpaw.{side}"):
            pc = joints[paw] + V((0, -r * 1.1, -r * 0.5))
            bpy.ops.mesh.primitive_cube_add(location=pc)
            toe = bpy.context.active_object
            toe.scale = (r * 0.9, r * 1.3, r * 0.5)
            parts.append(toe)

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

    # 実現メトリクスはサロゲートと一致させるため解析値を採用（tris のみ実値で上書き）。
    realized = predict_metrics(p)
    realized["tris"] = sum(max(0, len(poly.vertices) - 2) for poly in body.data.polygons)
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
