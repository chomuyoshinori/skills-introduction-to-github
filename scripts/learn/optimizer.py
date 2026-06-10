"""試行錯誤でブロッキングを最適化する学習ループ（bpy 必須）。

各試行: パラメータ提案 → (学習済み制約で事前補正) → 生成 → 検査 → 採点 → 記録。
成功も失敗も attempts.jsonl に永続記録し、lessons(知識ベース)を更新する。
再実行すると過去の記録/知見を読み込んで継続学習する。

使い方:
    python scripts/learn/optimizer.py -- \
        --asset assets/characters/goblin-warrior --iters 30 [--seed 0]
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.learn import lessons as L  # noqa: E402
from scripts.lib import scoring  # noqa: E402
from scripts.lib.anatomy import check_pose, load_anatomy  # noqa: E402
from scripts.lib.meshcheck import validate_scene_meshes  # noqa: E402
from scripts.lib.standards import load_standards, _mini_yaml_parse  # noqa: E402


def _parse_args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    args = {"asset": None, "iters": 30, "seed": None}
    it = iter(argv)
    for tok in it:
        if tok == "--asset":
            args["asset"] = next(it)
        elif tok == "--iters":
            args["iters"] = int(next(it))
        elif tok == "--seed":
            args["seed"] = int(next(it))
    return args


def _load_asset_meta(asset_dir):
    path = os.path.join(asset_dir, "asset.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return _mini_yaml_parse(f.read())


def _load_generator(meta):
    """asset.yaml の generator キーで生成器モジュールを選ぶ。"""
    if meta.get("generator") == "quadruped":
        from scripts.lib import quadruped as G
    else:
        from scripts.lib import humanoid as G
    return G


def _propose(rng, lessons, explore, G):
    """過去の知見から次のパラメータを提案する。"""
    bounds = G.PARAM_BOUNDS
    best = lessons.get("best")
    sweet = lessons.get("sweet_spot") or {}

    if best and not explore:
        # ベスト周辺を突然変異（局所探索）
        base = best["params"]
        params = {}
        for k, (lo, hi) in bounds.items():
            sigma = (hi - lo) * 0.12
            params[k] = base.get(k, (lo + hi) / 2) + rng.gauss(0, sigma)
    elif sweet and rng.random() < 0.5:
        # sweet spot 周辺を広めに探索
        params = {}
        for k, (lo, hi) in bounds.items():
            sigma = (hi - lo) * 0.25
            params[k] = sweet.get(k, (lo + hi) / 2) + rng.gauss(0, sigma)
    else:
        # 一様ランダム（広域探索）。失敗領域も踏みに行き、そこから制約を学ぶ。
        params = {k: rng.uniform(lo, hi) for k, (lo, hi) in bounds.items()}

    return G.clamp_params(params)


def main():
    import bpy  # noqa: F401

    args = _parse_args(sys.argv)
    assert args["asset"], "--asset を指定してください"
    rng = random.Random(args["seed"])

    asset_dir = os.path.abspath(args["asset"])
    meta = _load_asset_meta(asset_dir)
    atype = meta.get("type", "npc_character")
    target = meta.get("target") or {}
    if not target:
        print("[optimizer] 警告: asset.yaml に target が無いため既定値を使用")
        target = {"height_m": 1.3, "head_ratio": 0.24, "torso_ratio": 0.34,
                  "leg_ratio": 0.40, "arm_ratio": 0.38, "shoulder_w": 0.2, "lean_deg": 12}

    std = load_standards()
    budget = std["poly_budget"].get(atype)
    anatomy = load_anatomy()
    species = meta.get("species", "human")
    G = _load_generator(meta)
    # critic ループが目標を更新していれば、それを上書き適用する
    wt_path = os.path.join(asset_dir, "learn", "working_target.json")
    if os.path.exists(wt_path):
        with open(wt_path, encoding="utf-8") as f:
            target = {**target, **json.load(f)}
        print(f"[optimizer] working_target.json を適用（critic 更新済み目標）")
    # オブジェクト/マテリアル命名に使う識別子（CHR_<name>_... 規則に適合させる）
    model_name = re.sub(r"[^a-z0-9]+", "_", str(meta.get("name", "asset")).lower()).strip("_")

    learn_dir = os.path.join(asset_dir, "learn")
    os.makedirs(learn_dir, exist_ok=True)
    attempts_path = os.path.join(learn_dir, "attempts.jsonl")
    lessons_path = os.path.join(learn_dir, "lessons.json")
    md_path = os.path.join(learn_dir, "LESSONS.md")

    lessons = L.load(lessons_path)
    start_total = lessons["stats"]["total"]
    avoided = 0

    print(f"[optimizer] asset={meta.get('name')} type={atype} budget={budget} "
          f"目標={target.get('height_m')}m / 既存試行={start_total}")

    # 途中クラッシュでもその時点までの知見を失わないよう、
    # 定期保存＋finally 保存で永続化を保証する（save はアトミック）。
    try:
        with open(attempts_path, "a", encoding="utf-8") as log:
            for i in range(args["iters"]):
                explore = (rng.random() < 0.3) or (lessons.get("best") is None)
                params = _propose(rng, lessons, explore, G)
                # 学習済み制約で事前補正（= 既知の失敗を回避）
                params, applied = L.apply_constraints(lessons, params)
                if applied:
                    avoided += 1

                # 解剖学検査（関節可動域）。違反ならメッシュ生成せず失敗として学習。
                violations = check_pose(params, species=species, anatomy=anatomy)
                if violations:
                    valid = {"ok": False, "fail_kinds": {"anatomy"}, "tris": None,
                             "failures": [f"{v['joint']}: {v['value']}° は可動域外"
                                          for v in violations]}
                    realized = None
                else:
                    realized = G.build(params, name=model_name)["realized"]
                    valid = validate_scene_meshes(std, atype)
                sc = scoring.score_attempt(realized or {}, target, valid, budget)

                attempt = {
                    "t": round(time.time(), 1),
                    "params": params,
                    "realized": realized,
                    "score": sc["score"],
                    "valid": sc["valid"],
                    "fail_kinds": sc.get("fail_kinds", []),
                    "violations": violations,
                    "applied_lessons": applied,
                }
                log.write(json.dumps(attempt, ensure_ascii=False) + "\n")
                log.flush()
                L.update(lessons, attempt, target)

                tag = "OK " if sc["valid"] else "FAIL"
                if sc["valid"]:
                    extra = f"prop_err={sc['prop_error']}"
                elif violations:
                    extra = "anatomy:" + ",".join(
                        f"{v['joint']}={v['value']}°" for v in violations)
                else:
                    extra = "/".join(sc["fail_kinds"])
                note = f"  ←補正:{applied}" if applied else ""
                size = params.get("height_m") or params.get("body_length_m") or 0
                print(f"  [{start_total + i + 1:>3}] {tag} score={sc['score']:>7} "
                      f"seg={params['seg']:>3} size={size:.2f} {extra}{note}")

                if (i + 1) % 10 == 0:
                    L.save(lessons, lessons_path)

    finally:
        L.save(lessons, lessons_path)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(L.to_markdown(lessons))

    # ベストを保存（再生成して .blend 出力）
    best = lessons.get("best")
    if best:
        G.build(best["params"], name=model_name)
        out_blend = os.path.join(asset_dir, "highpoly", "base.blend")
        G.save(out_blend)
        print(f"[optimizer] ベスト(score={best['score']}) を保存: {out_blend}")

    st = lessons["stats"]
    print(f"[optimizer] 完了: 通算{st['total']}試行 成功{st['valid']}/失敗{st['failed']} "
          f"事前回避{avoided}回  best={best['score'] if best else None}")
    print(f"[optimizer] 知見: {lessons_path} / {md_path}")


if __name__ == "__main__":
    main()
