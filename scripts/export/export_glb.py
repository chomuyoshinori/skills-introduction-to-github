"""検査済みの blend を glb で書き出す Blender スクリプト。

使い方:
    blender --background --python scripts/export/export_glb.py -- \
        --blend assets/characters/my-goblin/lowpoly/lowpoly.blend \
        --out  assets/characters/my-goblin/export/my-goblin.glb

トランスフォーム/モディファイア適用は standards.yaml の export 設定に従う。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.lib.blendio import open_blend  # noqa: E402
from scripts.lib.standards import load_standards  # noqa: E402


def _parse_args(argv: list[str]) -> dict:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    args = {"blend": None, "out": "out.glb"}
    it = iter(argv)
    for tok in it:
        if tok == "--blend":
            args["blend"] = next(it)
        elif tok == "--out":
            args["out"] = next(it)
    return args


def main() -> None:
    import bpy

    args = _parse_args(sys.argv)
    std = load_standards()
    exp = std.get("export", {})

    if args["blend"]:
        open_blend(args["blend"])

    out = os.path.abspath(args["out"])
    os.makedirs(os.path.dirname(out), exist_ok=True)

    bpy.ops.export_scene.gltf(
        filepath=out,
        export_format="GLB",
        export_apply=bool(exp.get("apply_modifiers", True)),
        export_yup=True,
    )
    print(f"[export] saved: {out}")


if __name__ == "__main__":
    main()
