"""Blender 不要のアセットメタ検査（CI 用）。

各 assets/**/asset.yaml を読み、standards.yaml と矛盾がないかを検査する。
Blender を起動しないので CI で高速に回せる。メッシュ自体の検査は
scripts/checks/validate_mesh.py（Blender 必要）が担当する。

使い方:
    python scripts/checks/validate_assets.py
失敗時は終了コード 1。
"""
from __future__ import annotations

import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.lib.standards import load_standards  # noqa: E402

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_yaml(path: str) -> dict:
    try:
        import yaml  # type: ignore

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ModuleNotFoundError:
        from scripts.lib.standards import _mini_yaml_parse

        with open(path, "r", encoding="utf-8") as f:
            return _mini_yaml_parse(f.read())


def main() -> int:
    std = load_standards()
    valid_types = set(std["poly_budget"].keys())
    units = std["units"]
    prefix_re = re.compile(r"^(CHR|PRP)_[a-z0-9]+(_[a-z0-9]+)*$")

    asset_files = sorted(
        glob.glob(os.path.join(REPO_ROOT, "assets", "**", "asset.yaml"), recursive=True)
    )
    failures: list[str] = []
    checked = 0

    for path in asset_files:
        rel = os.path.relpath(path, REPO_ROOT)
        folder = os.path.basename(os.path.dirname(path))
        # テンプレートはスケルトンなので type/prefix 以外は緩く扱う
        is_template = folder.startswith("_")
        meta = _load_yaml(path)
        checked += 1

        atype = meta.get("type")
        if atype not in valid_types:
            failures.append(f"{rel}: 不正な type '{atype}'（許容: {sorted(valid_types)}）")

        prefix = meta.get("prefix", "")
        if not prefix_re.match(str(prefix)):
            failures.append(f"{rel}: prefix '{prefix}' が命名規則に反しています")

        if not is_template:
            name = str(meta.get("name", ""))
            if name and name != folder:
                failures.append(f"{rel}: name '{name}' がフォルダ名 '{folder}' と不一致")

            h = meta.get("height_m")
            if isinstance(h, (int, float)):
                if not (units["character_height_min"] <= h <= units["character_height_max"]):
                    failures.append(
                        f"{rel}: height_m {h} が許容範囲外 "
                        f"({units['character_height_min']}–{units['character_height_max']})"
                    )

    print(f"[validate_assets] checked {checked} asset.yaml file(s)")
    if failures:
        print("[validate_assets] FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("[validate_assets] OK ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
