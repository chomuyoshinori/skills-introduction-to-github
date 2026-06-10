"""blend のプレビュー画像を 3/4 アングルでレンダリングする Blender スクリプト。

使い方:
    blender --background --python scripts/preview/render.py -- \
        --blend assets/characters/my-goblin/blocking/blocking.blend \
        --out  assets/characters/my-goblin/concept/preview.png

レンダリング本体は scripts/lib/viz.py（視覚レビューと共用）。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.lib.blendio import open_blend  # noqa: E402
from scripts.lib.viz import render_scene  # noqa: E402


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

    args = _parse_args(sys.argv)
    if args["blend"]:
        open_blend(args["blend"])
    out = render_scene(args["out"], args["res"])
    print(f"[preview] saved: {out}")


if __name__ == "__main__":
    main()
