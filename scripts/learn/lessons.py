"""試行から学ぶ永続的な知識ベース（lessons）。

失敗 → 回避すべき制約（パラメータ上限/範囲）を抽出。
成功 → 良パラメータ域（sweet spot）を更新。
JSON で永続化し、人間向けに LESSONS.md も出力する。bpy 非依存。
"""
from __future__ import annotations

import json
import os
from typing import Any

EMPTY: dict[str, Any] = {
    "version": 1,
    "constraints": {
        # ポリゴン予算の実行可能境界を二分探索的に学習する。
        "seg_cap": None,        # 採用する安全上限（成功上限と失敗下限の中点）
        "seg_max_pass": None,   # 予算内に収まった最大 seg
        "seg_min_fail": None,   # 予算超過した最小 seg
        # スケール検査を通した安全な height レンジ（失敗から狭める）
        "height_floor": None,
        "height_ceil": None,
        # 解剖学検査の違反から学んだ、パラメータごとの実行可能レンジ。
        # 提案側は可動域(ROM)を知らないが、違反を踏むたびにここが狭まる。
        "param_ranges": {},
    },
    "sweet_spot": {},      # 上位成功例のパラメータ平均
    "best": None,          # これまでの最良 attempt
    "stats": {"total": 0, "valid": 0, "failed": 0, "by_kind": {}},
    "top_k": [],           # 上位成功 attempt（params, score）
}

TOP_K = 5


def load(path: str) -> dict[str, Any]:
    """知識ベースを読み込む。破損していたら退避して空から再開する（学習を止めない）。"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            backup = path + ".corrupt"
            os.replace(path, backup)
            print(f"[lessons] 警告: {path} が破損していたため {backup} に退避 ({e})")
    return json.loads(json.dumps(EMPTY))  # deep copy


def save(lessons: dict[str, Any], path: str) -> None:
    """アトミックに保存する（書き込み途中のクラッシュで破損させない）。"""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def update(lessons: dict[str, Any], attempt: dict[str, Any], target: dict[str, Any]) -> None:
    """1試行の結果で知識ベースを更新する。"""
    st = lessons["stats"]
    st["total"] += 1
    params = attempt["params"]
    cons = lessons["constraints"]

    if attempt["valid"]:
        st["valid"] += 1
        # 成功 → 予算内に収まった seg の上限を更新（実行可能境界の下側）
        seg = params.get("seg")
        if seg is not None:
            cons["seg_max_pass"] = seg if cons["seg_max_pass"] is None else max(cons["seg_max_pass"], seg)
            _recompute_seg_cap(cons)
        # 成功 → 上位 K を更新し sweet spot を再計算
        tk = lessons["top_k"]
        tk.append({"params": params, "score": attempt["score"]})
        tk.sort(key=lambda a: a["score"], reverse=True)
        del tk[TOP_K:]
        keys = params.keys()
        lessons["sweet_spot"] = {
            k: round(sum(a["params"][k] for a in tk) / len(tk), 4) for k in keys
        }
        if lessons["best"] is None or attempt["score"] > lessons["best"]["score"]:
            lessons["best"] = {"params": params, "score": attempt["score"],
                               "realized": attempt.get("realized")}
    else:
        st["failed"] += 1
        for kind in attempt["fail_kinds"]:
            st["by_kind"][kind] = st["by_kind"].get(kind, 0) + 1
            # 失敗 → 制約を学習
            if kind == "budget":
                seg = params.get("seg")
                if seg is not None:
                    cons["seg_min_fail"] = seg if cons["seg_min_fail"] is None else min(cons["seg_min_fail"], seg)
                    _recompute_seg_cap(cons)
            elif kind == "anatomy":
                # 関節可動域の違反 → そのパラメータの実行可能レンジを狭める
                for vio in attempt.get("violations", []):
                    pr = cons.setdefault("param_ranges", {}).setdefault(
                        vio["param"], {"lo": None, "hi": None})
                    v = vio["value"]
                    if vio["bound"] == "max":  # 上限超え → 学習上限を引き下げ
                        pr["hi"] = v if pr["hi"] is None else min(pr["hi"], v)
                    else:                       # 下限割れ → 学習下限を引き上げ
                        pr["lo"] = v if pr["lo"] is None else max(pr["lo"], v)
            elif kind == "scale":
                # 生成器のサイズ駆動パラメータ（humanoid: height_m / quadruped: body_length_m）
                size_key = "height_m" if "height_m" in params else "body_length_m"
                h = params.get(size_key)
                tgt = float(target.get(size_key, 1.3))
                if h is not None:
                    if h < tgt:  # 低すぎて失敗 → 下限を引き上げ
                        cons["height_floor"] = h if cons["height_floor"] is None else max(cons["height_floor"], h)
                    else:        # 高すぎて失敗 → 上限を引き下げ
                        cons["height_ceil"] = h if cons["height_ceil"] is None else min(cons["height_ceil"], h)


def _recompute_seg_cap(cons: dict[str, Any]) -> None:
    """実行可能境界を成功上限と失敗下限から二分探索的に推定する。"""
    lo, hi = cons.get("seg_max_pass"), cons.get("seg_min_fail")
    if hi is None:
        return  # まだ失敗していなければ上限を設けない
    if lo is not None and lo < hi:
        cons["seg_cap"] = int((lo + hi) // 2)  # 境界の中点を安全上限に
    else:
        cons["seg_cap"] = hi - 1


def apply_constraints(lessons: dict[str, Any], params: dict[str, float]) -> tuple[dict[str, float], list[str]]:
    """学習済み制約を提案パラメータに適用。変更点を返す（= 失敗の事前回避）。"""
    cons = lessons["constraints"]
    out = dict(params)
    applied: list[str] = []
    if cons.get("seg_cap") is not None and out.get("seg", 0) >= cons["seg_cap"]:
        out["seg"] = max(6, cons["seg_cap"] - 1)
        applied.append(f"seg→{out['seg']} (予算超過回避)")
    size_key = "height_m" if "height_m" in out else "body_length_m"
    if cons.get("height_floor") is not None and out.get(size_key, 0) <= cons["height_floor"]:
        out[size_key] = cons["height_floor"] + 0.05
        applied.append(f"{size_key}→{out[size_key]:.2f} (低すぎ回避)")
    if cons.get("height_ceil") is not None and out.get(size_key, 0) >= cons["height_ceil"]:
        out[size_key] = cons["height_ceil"] - 0.05
        applied.append(f"{size_key}→{out[size_key]:.2f} (高すぎ回避)")
    # 解剖学違反から学んだ実行可能レンジに収める（margin: 学習境界は真の限界より
    # 外側にあり得るため、少し内側に寄せて再違反の確率を下げる）
    for param, pr in cons.get("param_ranges", {}).items():
        v = out.get(param)
        if v is None:
            continue
        margin = 4.0 if param.endswith("_deg") else 0.02
        if pr.get("hi") is not None and v >= pr["hi"]:
            out[param] = pr["hi"] - margin
            applied.append(f"{param}→{out[param]:.1f} (可動域学習)")
        elif pr.get("lo") is not None and v <= pr["lo"]:
            out[param] = pr["lo"] + margin
            applied.append(f"{param}→{out[param]:.1f} (可動域学習)")
    return out, applied


def to_markdown(lessons: dict[str, Any]) -> str:
    cons = lessons["constraints"]
    st = lessons["stats"]
    lines = ["# 学習済み知見 (LESSONS)", "",
             "> このファイルは scripts/learn/optimizer.py が自動生成します。", ""]
    lines.append("## 統計")
    lines.append(f"- 総試行: {st['total']} / 成功: {st['valid']} / 失敗: {st['failed']}")
    if st["by_kind"]:
        kinds = ", ".join(f"{k}:{v}" for k, v in sorted(st["by_kind"].items()))
        lines.append(f"- 失敗の内訳: {kinds}")
    lines += ["", "## 失敗から学んだ制約"]
    if cons.get("seg_cap") is not None:
        lines.append(f"- **seg < {cons['seg_cap']}**: これ以上はポリゴン予算を超過した")
    if cons.get("height_floor") is not None:
        lines.append(f"- **height ≥ {cons['height_floor']:.2f}m**: これ未満はスケール検査に落ちた")
    if cons.get("height_ceil") is not None:
        lines.append(f"- **height ≤ {cons['height_ceil']:.2f}m**: これ超はスケール検査に落ちた")
    for param, pr in sorted(cons.get("param_ranges", {}).items()):
        lo = f"{pr['lo']:.1f} <" if pr.get("lo") is not None else ""
        hi = f"< {pr['hi']:.1f}" if pr.get("hi") is not None else ""
        lines.append(f"- **{lo} {param} {hi}**: 可動域違反から学習した実行可能レンジ")
    if (all(cons.get(k) is None for k in ("seg_cap", "height_floor", "height_ceil"))
            and not cons.get("param_ranges")):
        lines.append("- （まだ制約を学習していません）")
    lines += ["", "## 成功から学んだ良パラメータ域 (sweet spot)"]
    if lessons["sweet_spot"]:
        for k, v in lessons["sweet_spot"].items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- （まだ十分な成功例がありません）")
    if lessons.get("best"):
        b = lessons["best"]
        lines += ["", "## 現在のベスト", f"- スコア: **{b['score']}**",
                  "- params:", "  ```json", "  " + json.dumps(b["params"], ensure_ascii=False),
                  "  ```"]
    return "\n".join(lines) + "\n"
