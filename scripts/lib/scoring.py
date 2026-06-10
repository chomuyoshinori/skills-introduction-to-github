"""生成結果を目標仕様(target)に照らして採点する（bpy 非依存）。

スコア設計:
  - 検査に通らなければ大きな負のスコア（失敗として記録し、原因を学習に回す）
  - 通れば 100 を上限に、プロポーション誤差とポリゴン消費でペナルティ
目標は asset.yaml の `target` ブロックで定義する。
"""
from __future__ import annotations

from typing import Any

# プロポーション項目と重み（合計1.0）
PROP_WEIGHTS = {
    "head_ratio": 0.24,   # ゴブリンらしさは頭比率が支配的
    "height_m": 0.20,     # 目標の全高に合わせる
    "leg_ratio": 0.16,
    "torso_ratio": 0.12,
    "arm_ratio": 0.12,
    "shoulder_w": 0.08,
    "lean_deg": 0.08,
}


def proportion_error(realized: dict[str, Any], target: dict[str, Any]) -> float:
    """重み付き相対誤差（0=完全一致）。"""
    err = 0.0
    for key, w in PROP_WEIGHTS.items():
        if key not in target:
            continue
        tgt = float(target[key])
        cur = float(realized.get(key, 0.0))
        denom = abs(tgt) if abs(tgt) > 1e-6 else 1.0
        err += w * abs(cur - tgt) / denom
    return err


def score_attempt(
    realized: dict[str, Any],
    target: dict[str, Any],
    valid: dict[str, Any],
    budget: int | None,
) -> dict[str, Any]:
    """採点して内訳を返す。"""
    if not valid["ok"]:
        # 失敗は負スコア。原因数に応じて深くする（学習で回避対象）。
        s = -10.0 - 5.0 * len(valid["fail_kinds"])
        return {
            "score": round(s, 2),
            "valid": False,
            "prop_error": None,
            "tris": valid.get("tris"),
            "fail_kinds": sorted(valid["fail_kinds"]),
        }

    perr = proportion_error(realized, target)
    tris = valid.get("tris", 0)
    poly_penalty = 5.0 * (tris / budget) if budget else 0.0  # 予算消費が少ないほど良い
    score = 100.0 - 100.0 * perr - poly_penalty
    return {
        "score": round(score, 2),
        "valid": True,
        "prop_error": round(perr, 4),
        "poly_penalty": round(poly_penalty, 2),
        "tris": tris,
        "fail_kinds": [],
    }
