"""ブロッキング雛形を生成する Blender スクリプト。

使い方:
    blender --background --python scripts/generate/blocking.py -- \
        --out assets/characters/my-goblin/blocking/blocking.blend \
        --height 1.7 --type CHR --name goblin

`config/standards.yaml` の基準スケールに沿って、原点に立つ
ヒューマノイドのプリミティブ（胴・頭・四肢）を配置する。
ここからプロポーションを調整してハイポリへ進む。
"""
from __future__ import annotations

import os
import sys


def _parse_args(argv: list[str]) -> dict:
    # Blender は "--" 以降をスクリプト引数として渡す
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    args = {"out": "blocking.blend", "height": 1.7, "type": "CHR", "name": "asset"}
    it = iter(argv)
    for tok in it:
        if tok == "--out":
            args["out"] = next(it)
        elif tok == "--height":
            args["height"] = float(next(it))
        elif tok == "--type":
            args["type"] = next(it)
        elif tok == "--name":
            args["name"] = next(it)
    return args


def main() -> None:
    import bpy  # Blender 内でのみ利用可能

    args = _parse_args(sys.argv)
    h = args["height"]
    prefix = f"{args['type']}_{args['name']}"

    # シーンを空にしてメートル単位に設定
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0

    def add_part(part: str, location, scale):
        bpy.ops.mesh.primitive_cube_add(location=location)
        obj = bpy.context.active_object
        obj.scale = scale
        obj.name = f"{prefix}_{part}_LOD0"
        return obj

    # おおまかな人体比率（頭身ベース）で配置
    add_part("legs", (0, 0, h * 0.25), (h * 0.06, h * 0.06, h * 0.25))
    add_part("torso", (0, 0, h * 0.62), (h * 0.10, h * 0.06, h * 0.18))
    add_part("head", (0, 0, h * 0.90), (h * 0.06, h * 0.06, h * 0.07))
    add_part("arm_l", (h * 0.16, 0, h * 0.62), (h * 0.04, h * 0.04, h * 0.18))
    add_part("arm_r", (-h * 0.16, 0, h * 0.62), (h * 0.04, h * 0.04, h * 0.18))

    out = os.path.abspath(args["out"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"[blocking] saved: {out}")


if __name__ == "__main__":
    main()
