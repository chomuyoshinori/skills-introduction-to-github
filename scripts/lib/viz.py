"""現在の Blender シーンをプレビュー用にレンダリングする共通モジュール（bpy 必須）。

preview/render.py（CLI）と learn/visual_review.py（AI採点用）が共用する。
ヘッドレス環境(GPU/EGL なし)でも動くよう Cycles/CPU・低サンプルを既定にする。
"""
from __future__ import annotations

import math
import os


def render_scene(out: str, res: int = 600) -> str:
    """3/4 アングルにカメラ/ライトを置いてレンダリングし、出力パスを返す。"""
    import bpy
    import mathutils

    V = mathutils.Vector
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    center = V((0, 0, 0))
    height = 2.0
    if meshes:
        mn = V((1e9, 1e9, 1e9))
        mx = V((-1e9, -1e9, -1e9))
        for o in meshes:
            for c in o.bound_box:
                w = o.matrix_world @ V(c)
                mn = V((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
                mx = V((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
        center = (mn + mx) / 2
        height = max(mx.z - mn.z, mx.y - mn.y, mx.x - mn.x, 0.2)

    light_data = bpy.data.lights.new("key", type="SUN")
    light_data.energy = 3.0
    light = bpy.data.objects.new("key", light_data)
    light.rotation_euler = (math.radians(55), 0, math.radians(40))
    bpy.context.collection.objects.link(light)

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    dist = height * 2.2
    cam.location = center + V((dist * 0.8, -dist, height * 0.4))
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.device = "CPU"
    scene.render.resolution_x = res
    scene.render.resolution_y = res

    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    return out
