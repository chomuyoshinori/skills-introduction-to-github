"""Blend 内のメッシュを standards.yaml に照らして検査する Blender スクリプト（CLI）。

使い方:
    blender --background --python scripts/checks/validate_mesh.py -- \
        --blend assets/characters/my-goblin/lowpoly/lowpoly.blend \
        --type npc_character

合否を標準出力に出し、失敗時は終了コード 1 で抜ける（CI で利用可能）。
検査ロジック本体は scripts/lib/meshcheck.py（学習ループと共用）。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.lib.meshcheck import validate_scene_meshes  # noqa: E402
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
    import bpy  # noqa: F401  (pip 版 bpy では meshcheck の前に import が必要)

    args = _parse_args(sys.argv)
    std = load_standards()
    if args["blend"]:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args["blend"]))

    result = validate_scene_meshes(std, args["type"])
    print(f"[validate] tris={result['tris']} type={args['type']} "
          f"budget={std['poly_budget'].get(args['type'])}")
    if not result["ok"]:
        print("[validate] FAILED:")
        for f in result["failures"]:
            print(f"  - {f}")
        sys.exit(1)
    print("[validate] OK ✅")


if __name__ == "__main__":
    main()
