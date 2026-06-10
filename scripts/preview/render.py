"""blend のプレビュー画像を 3/4 アングルでレンダリングする Blender スクリプト。

使い方:
    blender --background --python scripts/preview/render.py -- \
        --blend assets/characters/my-goblin/blocking/blocking.blend \
        --out  assets/characters/my-goblin/concept/preview.png

ブロッキングやリトポの確認、AI(modeler) レビューへの添付画像に使う。
"""
from __future__ import annotations

import math
import os
import sys


def _parse_args(argv: list[str]) -> dict:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    args = {"blend": None, "out": "preview.png", "res": 512}
    it = iter(argv)
    for tok in it:
        if tok == "--blend":
            args["blend"] = next(it)
        elif tok == "--out":
            args["out"] = next(it)
        elif tok == "--res":
            args["res"] = int(next(it))
    return args


def main() -> None:
    import bpy
    import mathutils

    args = _parse_args(sys.argv)
    if args["blend"]:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args["blend"]))

    # 対象メッシュの中心と高さを推定し、カメラを 3/4 前方に配置
    zs, center = [], mathutils.Vector((0, 0, 0))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if meshes:
        mn = mathutils.Vector((1e9, 1e9, 1e9))
        mx = mathutils.Vector((-1e9, -1e9, -1e9))
        for o in meshes:
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                mn = mathutils.Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
                mx = mathutils.Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
        center = (mn + mx) / 2
        zs = [mn.z, mx.z]
    height = (zs[1] - zs[0]) if zs else 2.0

    # ライト
    light_data = bpy.data.lights.new("key", type="SUN")
    light_data.energy = 3.0
    light = bpy.data.objects.new("key", light_data)
    light.rotation_euler = (math.radians(55), 0, math.radians(40))
    bpy.context.collection.objects.link(light)

    # カメラ
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    dist = height * 2.2
    cam.location = center + mathutils.Vector((dist * 0.8, -dist, height * 0.4))
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    # ヘッドレス(GPU/EGL なし)でも確実に動くよう Cycles/CPU を既定にする。
    # 低サンプルのプレビュー用途なので速度は十分。
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.device = "CPU"
    scene.render.resolution_x = args["res"]
    scene.render.resolution_y = args["res"]
    scene.render.film_transparent = False

    out = os.path.abspath(args["out"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"[preview] saved: {out}")


if __name__ == "__main__":
    main()
