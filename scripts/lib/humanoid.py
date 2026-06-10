"""パラメトリックな多関節ヒューマノイド生成器。

球(関節)＋円柱(骨格セグメント)で人体を組む。股関節・膝・肩・肘・体幹の
角度パラメータでポーズが付き、関節位置は前方/屈曲の運動学で計算する。
あわせてアーマチュア(ボーン)を生成し、config/anatomy.yaml の可動域を
Limit Rotation 制約としてリグに焼き込む（= 解剖学知識のリグへの反映）。

円柱のフタは TRIFAN で Ngon を避け、各パーツは閉じた多様体メッシュ。
学習ループ(scripts/learn/)がパラメータを探索する対象。bpy 必須。
"""
from __future__ import annotations

import math
from typing import Any

# 探索対象パラメータの定義域（min, max）。
# height/seg は検査限界を、関節角は解剖学的可動域(config/anatomy.yaml)を
# わざと超える広さにしてある。実際の失敗（スケール落ち/予算超過/解剖学violation）
# を踏ませて、学習ループがそこから制約・可動域を学べるようにする狙い。
PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "height_m": (0.2, 3.5),
    "head_ratio": (0.14, 0.30),
    "torso_ratio": (0.28, 0.42),
    "leg_ratio": (0.34, 0.50),
    "arm_ratio": (0.30, 0.46),
    "shoulder_w": (0.12, 0.30),
    "limb_radius": (0.04, 0.11),
    "seg": (6, 200),
    # ポーズ角（度）。可動域外は解剖学検査に落ちる（例: 膝の逆関節）
    "lean_deg": (-50, 70),           # 体幹 ROM: -30..45
    "hip_pitch_deg": (-60, 150),     # 股関節 ROM: -20..120
    "knee_bend_deg": (-40, 180),     # 膝 ROM: 0..150（負=過伸展は不可）
    "shoulder_pitch_deg": (-100, 210),  # 肩 ROM: -60..180
    "elbow_bend_deg": (-40, 180),    # 肘 ROM: 0..145
}

POSE_KEYS = ("lean_deg", "hip_pitch_deg", "knee_bend_deg",
             "shoulder_pitch_deg", "elbow_bend_deg")


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

    build() が返すものと同じ realized dict を返す。学習ループの探索はこれを使い、
    実メッシュの生成は候補/最終確定時のみ bpy で行う（スピード最適化）。
    """
    import math

    p = clamp_params(params)
    H = p["height_m"]
    r = p["limb_radius"]
    leg_len = p["leg_ratio"] * H
    torso_len = p["torso_ratio"] * H
    head_d = p["head_ratio"] * H
    arm_len = p["arm_ratio"] * H
    thigh_len, shank_len = leg_len * 0.52, leg_len * 0.48

    lean = math.radians(p["lean_deg"])
    hip_pitch = math.radians(p["hip_pitch_deg"])
    knee_bend = math.radians(p["knee_bend_deg"])

    # 脚の運動学（dir_down の z 成分 = -cos）で骨盤高を求める
    drop = thigh_len * (-math.cos(hip_pitch)) + shank_len * (-math.cos(hip_pitch - knee_bend))
    pelvis_z = -drop + r
    neck_z = pelvis_z + torso_len * math.cos(lean)
    head_center_z = neck_z + (head_d / 2 + r * 0.3) * math.cos(lean)
    head_top_z = head_center_z + (head_d / 2) * math.cos(lean)
    foot_bottom_z = r - r * 1.1  # 足首球の下端（接地付近）
    realized_h = head_top_z - foot_bottom_z

    seg = max(3, p["seg"])
    # tris を実メッシュと厳密一致で算出（14球＋9円柱＋4立方体。実測フィット済み）
    R = max(3, seg // 2)
    tris = 14 * 2 * seg * (R - 1) + 36 * seg + 48

    realized = {
        "height_m": realized_h,
        "head_ratio": head_d / realized_h if realized_h else 0,
        "torso_ratio": torso_len / realized_h if realized_h else 0,
        "leg_ratio": leg_len / realized_h if realized_h else 0,
        "arm_ratio": arm_len / realized_h if realized_h else 0,
        "shoulder_w": p["shoulder_w"],
        "limb_radius": r,
        "tris": tris,
    }
    for k in POSE_KEYS:
        realized[k] = p[k]
    return realized


def build_humanoid(params: dict[str, float], name: str = "goblin",
                   with_rig: bool = True) -> dict[str, Any]:
    """params から多関節ヒューマノイドを生成し、実現メトリクスを返す。"""
    import bpy
    import mathutils

    V = mathutils.Vector
    p = clamp_params(params)
    H = p["height_m"]
    seg = max(3, p["seg"])
    r = p["limb_radius"]

    leg_len = p["leg_ratio"] * H
    torso_len = p["torso_ratio"] * H
    head_d = p["head_ratio"] * H
    arm_len = p["arm_ratio"] * H
    shoulder_w = p["shoulder_w"]
    thigh_len, shank_len = leg_len * 0.52, leg_len * 0.48
    upper_len, fore_len = arm_len * 0.52, arm_len * 0.48

    lean = math.radians(p["lean_deg"])
    hip_pitch = math.radians(p["hip_pitch_deg"])
    knee_bend = math.radians(p["knee_bend_deg"])
    sh_pitch = math.radians(p["shoulder_pitch_deg"])
    el_bend = math.radians(p["elbow_bend_deg"])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    parts: list[Any] = []

    def dir_down(a: float) -> Any:
        """真下からの前方ピッチ a（+で前方 = -Y 方向）の単位ベクトル。"""
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
        return obj

    def sphere(center, radius):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=seg, ring_count=max(3, seg // 2),
            radius=radius, location=center,
        )
        parts.append(bpy.context.active_object)

    # --- 運動学で関節位置を計算 ---
    # 脚: 大腿は股関節ピッチ、下腿は膝屈曲ぶん後方へ折れる
    thigh_dir = dir_down(hip_pitch)
    shank_dir = dir_down(hip_pitch - knee_bend)  # 膝屈曲は足を後方へ送る
    drop = thigh_len * thigh_dir.z + shank_len * shank_dir.z  # 負の量
    pelvis_z = -drop + r  # 足首がほぼ接地する高さに骨盤を置く
    pelvis = V((0, 0, pelvis_z))

    hip_x = shoulder_w * 0.5
    joints: dict[str, Any] = {"pelvis": pelvis}
    for side, sgn in (("L", 1), ("R", -1)):
        hip = pelvis + V((sgn * hip_x, 0, 0))
        knee = hip + thigh_len * thigh_dir
        ankle = knee + shank_len * shank_dir
        joints[f"hip.{side}"] = hip
        joints[f"knee.{side}"] = knee
        joints[f"ankle.{side}"] = ankle

    # 体幹: 骨盤から前傾(lean)して首へ
    up_dir = V((0, -math.sin(lean), math.cos(lean)))
    neck = pelvis + torso_len * up_dir
    joints["neck"] = neck
    head_center = neck + up_dir * (head_d / 2 + r * 0.3)
    joints["head_top"] = head_center + up_dir * (head_d / 2)

    # 腕: 肩ピッチで前後に振り、肘屈曲で前へ折れる
    upper_dir = dir_down(sh_pitch)
    fore_dir = dir_down(sh_pitch + el_bend)  # 肘屈曲は前腕を前方へ
    for side, sgn in (("L", 1), ("R", -1)):
        sh = neck + V((sgn * shoulder_w, 0, 0))
        elbow = sh + upper_len * upper_dir
        wrist = elbow + fore_len * fore_dir
        joints[f"shoulder.{side}"] = sh
        joints[f"elbow.{side}"] = elbow
        joints[f"wrist.{side}"] = wrist

    # --- メッシュ生成 ---
    cylinder_between(pelvis, neck, r * 1.7)            # 胴
    sphere(pelvis, r * 1.6)                            # 骨盤
    sphere(head_center, head_d / 2)                    # 頭
    for side in ("L", "R"):
        cylinder_between(joints[f"hip.{side}"], joints[f"knee.{side}"], r)
        cylinder_between(joints[f"knee.{side}"], joints[f"ankle.{side}"], r * 0.9)
        cylinder_between(joints[f"shoulder.{side}"], joints[f"elbow.{side}"], r * 0.8)
        cylinder_between(joints[f"elbow.{side}"], joints[f"wrist.{side}"], r * 0.7)
        sphere(joints[f"hip.{side}"], r * 1.1)         # 関節球
        sphere(joints[f"knee.{side}"], r * 0.95)
        sphere(joints[f"shoulder.{side}"], r * 1.0)
        sphere(joints[f"elbow.{side}"], r * 0.85)
        sphere(joints[f"ankle.{side}"], r * 1.1)       # 足首
        sphere(joints[f"wrist.{side}"], r * 0.85)      # 手首
        # 足: 足首から前方(-Y)へ伸びる箱（シルエットの完成度を上げる）
        foot_c = joints[f"ankle.{side}"] + V((0, -r * 1.6, -r * 0.6))
        bpy.ops.mesh.primitive_cube_add(location=foot_c)
        foot = bpy.context.active_object
        foot.scale = (r * 0.7, r * 1.7, r * 0.5)
        parts.append(foot)
        # 手: 手首から下方へ伸びる小箱（カリカチュアらしく大きめ）
        hand_c = joints[f"wrist.{side}"] + V((0, 0, -r * 1.1))
        bpy.ops.mesh.primitive_cube_add(location=hand_c)
        hand = bpy.context.active_object
        hand.scale = (r * 0.8, r * 0.5, r * 1.0)
        parts.append(hand)

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

    # --- 実現メトリクス ---
    # サロゲート(predict_metrics)と完全一致させるため解析値を採用。
    # ただし tris は実メッシュの正確な値で上書きする（確定検査の精度のため）。
    realized = predict_metrics(p)
    realized["tris"] = sum(max(0, len(poly.vertices) - 2) for poly in body.data.polygons)
    return {"realized": realized, "object_name": body.name, "joints": joints}


def _build_armature(joints: dict[str, Any], name: str) -> None:
    """関節位置からボーンを張り、解剖学的可動域を Limit Rotation 制約で焼き込む。"""
    import bpy

    from scripts.lib.anatomy import load_anatomy

    anatomy = load_anatomy().get("human", {}).get("joints", {})

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

    bone("spine", joints["pelvis"], joints["neck"])
    bone("head", joints["neck"], joints["head_top"], "spine")
    for s in ("L", "R"):
        bone(f"thigh.{s}", joints[f"hip.{s}"], joints[f"knee.{s}"], "spine")
        bone(f"shin.{s}", joints[f"knee.{s}"], joints[f"ankle.{s}"], f"thigh.{s}")
        bone(f"upper_arm.{s}", joints[f"shoulder.{s}"], joints[f"elbow.{s}"], "spine")
        bone(f"forearm.{s}", joints[f"elbow.{s}"], joints[f"wrist.{s}"], f"upper_arm.{s}")

    bpy.ops.object.mode_set(mode="POSE")
    bone_joint = {"spine": "spine_pitch", "thigh": "hip_pitch", "shin": "knee",
                  "upper_arm": "shoulder_pitch", "forearm": "elbow"}
    for pb in arm_obj.pose.bones:
        base = pb.name.split(".")[0]
        joint = bone_joint.get(base)
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


# 学習ループ向けの共通インターフェース（quadruped.build と同型）
build = build_humanoid
