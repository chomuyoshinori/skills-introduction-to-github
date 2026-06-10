"""関節の解剖学知識ベース(config/anatomy.yaml)の読み込みとポーズ検査（bpy 非依存）。

check_pose() は「このポーズは解剖学的に可能か」を判定する。
学習ループの提案側は可動域を知らず、この検査に落ちることで範囲を学習する。
"""
from __future__ import annotations

import os
from typing import Any

from scripts.lib.standards import _mini_yaml_parse

_DEFAULT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config", "anatomy.yaml")
)

# 生成パラメータ名 → 関節名 の対応
PARAM_TO_JOINT = {
    "lean_deg": "spine_pitch",
    "hip_pitch_deg": "hip_pitch",
    "knee_bend_deg": "knee",
    "shoulder_pitch_deg": "shoulder_pitch",
    "elbow_bend_deg": "elbow",
}


def load_anatomy(path: str | None = None) -> dict[str, Any]:
    path = path or _DEFAULT_PATH
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return _mini_yaml_parse(text)


def check_pose(
    pose_params: dict[str, float],
    species: str = "human",
    anatomy: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """ポーズの解剖学的妥当性を検査し、違反のリストを返す（空なら妥当）。

    違反: {"param", "joint", "value", "bound": "min"|"max", "limit"}
    """
    anatomy = anatomy or load_anatomy()
    joints = anatomy.get(species, {}).get("joints", {})
    violations: list[dict[str, Any]] = []
    for param, joint_name in PARAM_TO_JOINT.items():
        if param not in pose_params or joint_name not in joints:
            continue
        v = float(pose_params[param])
        j = joints[joint_name]
        if v < j["min_deg"]:
            violations.append({"param": param, "joint": joint_name, "value": round(v, 1),
                               "bound": "min", "limit": j["min_deg"]})
        elif v > j["max_deg"]:
            violations.append({"param": param, "joint": joint_name, "value": round(v, 1),
                               "bound": "max", "limit": j["max_deg"]})
    return violations
