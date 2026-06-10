"""批判的専門家(critic)と改善を繰り返す actor-critic ループ（オーケストレータ）。

1ラウンド =
  [actor]  optimizer が現在の目標へ向けて試行錯誤（subprocess, bpy）
  [render] 上位候補を visual_review がレンダリング（subprocess, bpy）
  [critic] AI が agents/critic.md の役割で learn/critique.json を書く（人/AI）
  [apply]  critique を目標の修正指示に変換し working_target.json を更新

critic の採点（加重平均）が challenge.yaml の pass_threshold 以上になれば合格。
関節可動域などの物理的知見(lessons.constraints)はラウンドを跨いで保持し、
「良さの定義」だけを更新する。bpy 非依存（重い処理は subprocess に委譲）。

使い方:
  # ラウンドのお膳立て（最適化＋候補レンダリング）
  python scripts/learn/critic_loop.py --asset assets/characters/goblin-warrior --setup
  #   → AI が learn/critique.json を作成（agents/critic.md 参照）
  # critique を適用して目標を更新
  python scripts/learn/critic_loop.py --asset assets/characters/goblin-warrior --apply
  # 現在の進捗を表示
  python scripts/learn/critic_loop.py --asset assets/characters/goblin-warrior --status
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.learn import lessons as L  # noqa: E402
from scripts.learn.optimizer import _load_asset_meta, _load_generator  # noqa: E402
from scripts.lib.standards import _mini_yaml_parse  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_challenge(asset_dir: str) -> dict:
    path = os.path.join(asset_dir, "challenge.yaml")
    with open(path, encoding="utf-8") as f:
        return _mini_yaml_parse(f.read())


def _current_target(asset_dir: str, meta: dict) -> dict:
    """working_target があればそれ、無ければ asset.yaml の target。"""
    wt = os.path.join(asset_dir, "learn", "working_target.json")
    target = dict(meta.get("target") or {})
    if os.path.exists(wt):
        with open(wt, encoding="utf-8") as f:
            target.update(json.load(f))
    return target


def _round_no(asset_dir: str) -> int:
    hist = os.path.join(asset_dir, "learn", "critique_history.jsonl")
    if not os.path.exists(hist):
        return 1
    with open(hist, encoding="utf-8") as f:
        return sum(1 for _ in f) + 1


def _run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=REPO)


def setup(asset_dir: str) -> None:
    meta = _load_asset_meta(asset_dir)
    ch = _load_challenge(asset_dir)
    rnd = _round_no(asset_dir)
    iters = int(ch.get("optimize_iters", 30))
    top = int(ch.get("top_candidates", 3))
    print(f"=== ラウンド {rnd}: actor 最適化({iters}試行) → 候補レンダリング({top}) ===")

    py = sys.executable
    _run([py, "scripts/learn/optimizer.py", "--",
          "--asset", asset_dir, "--iters", str(iters), "--seed", str(rnd)])
    _run([py, "scripts/learn/visual_review.py", "--",
          "--asset", asset_dir, "--top", str(top), "--recent", str(iters)])

    target = _current_target(asset_dir, meta)
    print(f"\n[critic_loop] 現在の目標値:\n  {json.dumps(target, ensure_ascii=False)}")
    print(f"[critic_loop] 課題: {ch.get('title')}")
    print(f"[critic_loop] ルーブリック: {ch.get('rubric')}  合格閾値={ch.get('pass_threshold')}")
    print("[critic_loop] → agents/critic.md の役割で各 cand_*.png を採点し、"
          f"\n               {os.path.join(asset_dir, 'learn', 'critique.json')} を作成して --apply を実行")


def _weighted_overall(scores: dict, rubric: dict) -> float:
    num = sum(float(scores.get(d, 0)) * float(w) for d, w in rubric.items())
    den = sum(float(w) for d in rubric for w in [rubric[d]] if d in scores)
    return round(num / den, 2) if den else 0.0


def apply(asset_dir: str) -> None:
    meta = _load_asset_meta(asset_dir)
    ch = _load_challenge(asset_dir)
    G = _load_generator(meta)  # bpy 非依存（PARAM_BOUNDS/clamp_params のみ使用）
    rubric = ch.get("rubric", {})
    threshold = float(ch.get("pass_threshold", 8.0))
    learn_dir = os.path.join(asset_dir, "learn")

    with open(os.path.join(learn_dir, "critique.json"), encoding="utf-8") as f:
        crit = json.load(f)

    scores = crit.get("scores", {})
    overall = _weighted_overall(scores, rubric)
    rnd = _round_no(asset_dir)

    # 修正指示を目標へ適用（生成器の定義域にクランプ）
    target = _current_target(asset_dir, meta)
    applied = []
    for d in crit.get("directives", []):
        param, delta = d.get("param"), d.get("delta")
        if param not in G.PARAM_BOUNDS:
            print(f"[critic_loop] 警告: 未知のパラメータ '{param}' をスキップ")
            continue
        before = target.get(param, sum(G.PARAM_BOUNDS[param]) / 2)
        target[param] = before + float(delta)
        applied.append({"param": param, "delta": delta, "issue": d.get("issue", "")})
    target = {k: v for k, v in G.clamp_params(target).items() if k in target}

    # 物理的知見(可動域・seg境界)は保持。top_k/sweet_spot は旧目標の産物なので破棄するが、
    # 旧ベストは新目標で再採点して探索のアンカーとして残す（R7: 毎回の全消しは収束を妨げた）。
    lessons_path = os.path.join(learn_dir, "lessons.json")
    if os.path.exists(lessons_path):
        lessons = L.load(lessons_path)
        lessons["top_k"] = []
        lessons["sweet_spot"] = {}
        best = lessons.get("best")
        if best and best.get("realized"):
            from scripts.lib.scoring import score_attempt
            from scripts.lib.standards import load_standards
            std = load_standards()
            budget = std["poly_budget"].get(meta.get("type", "npc_character"))
            valid = {"ok": True, "fail_kinds": set(),
                     "tris": best["realized"].get("tris", 0)}
            sc = score_attempt(best["realized"], target, valid, budget)
            lessons["best"] = {"params": best["params"], "score": sc["score"],
                               "realized": best["realized"]}
            print(f"[critic_loop] 旧ベストを新目標で再採点: {sc['score']}（アンカー保持）")
        else:
            lessons["best"] = None
        L.save(lessons, lessons_path)

    with open(os.path.join(learn_dir, "working_target.json"), "w", encoding="utf-8") as f:
        json.dump(target, f, ensure_ascii=False, indent=2)

    verdict = crit.get("verdict", "REVISE")
    passed = overall >= threshold or verdict == "ACCEPT"
    record = {"round": rnd, "scores": scores, "overall": overall,
              "verdict": verdict, "passed": passed,
              "summary": crit.get("summary", ""), "applied": applied,
              "new_target": target}
    with open(os.path.join(learn_dir, "critique_history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"=== ラウンド {rnd} の評価 ===")
    print(f"  各次元: {scores}")
    print(f"  加重平均: {overall} / 閾値 {threshold}  → {'合格 ✅' if passed else '改善継続 🔁'}")
    print(f"  講評: {crit.get('summary', '')}")
    for a in applied:
        print(f"  修正: {a['param']} {a['delta']:+} ({a['issue']})")
    if passed:
        print(f"[critic_loop] 課題クリア。working_target が最終目標。--setup で最終モデルを確定可。")
    else:
        print(f"[critic_loop] 次ラウンドへ: --setup を実行")


def finalize(asset_dir: str, cand_id: int) -> None:
    """critic が選んだ候補を最終モデルとして確定保存する（bpy 必須）。

    エンジン最良ではなく critic 承認の候補を base.blend にするための工程。
    critique.json に "best_candidate": <id> があれば --apply 後に自動で、
    無ければ手動で候補番号を指定して呼ぶ。
    """
    from scripts.learn.visual_review import _model_name
    from scripts.lib.viz import render_scene

    meta = _load_asset_meta(asset_dir)
    G = _load_generator(meta)
    name = _model_name(meta)
    learn_dir = os.path.join(asset_dir, "learn")
    with open(os.path.join(learn_dir, "review_request.json"), encoding="utf-8") as f:
        request = json.load(f)
    item = next((r for r in request if str(r["id"]) == str(cand_id)), None)
    if item is None:
        print(f"[critic_loop] 候補 {cand_id} が見つかりません")
        sys.exit(1)

    G.build(item["params"], name=name)
    out_blend = os.path.join(asset_dir, "highpoly", "base.blend")
    G.save(out_blend)
    G.build(item["params"], name=name)
    preview = os.path.join(asset_dir, "concept", "preview_critic_final.png")
    render_scene(preview, 600)
    print(f"[critic_loop] critic 承認候補 {cand_id} を確定: {out_blend}")
    print(f"[critic_loop] プレビュー: {preview}")


def status(asset_dir: str) -> None:
    hist = os.path.join(asset_dir, "learn", "critique_history.jsonl")
    if not os.path.exists(hist):
        print("[critic_loop] まだラウンド履歴がありません。--setup から開始してください。")
        return
    print("ラウンド | 加重平均 | 判定 | 講評")
    with open(hist, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            mark = "合格" if r["passed"] else "継続"
            print(f"  {r['round']:>4}  |  {r['overall']:>5}  | {mark} | {r['summary'][:40]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--setup", action="store_true", help="最適化＋候補レンダリング")
    g.add_argument("--apply", action="store_true", help="critique.json を適用")
    g.add_argument("--finalize", type=int, metavar="CAND",
                   help="critic 承認候補を最終モデルに確定（要 bpy）")
    g.add_argument("--status", action="store_true", help="進捗表示")
    args = ap.parse_args()
    asset_dir = os.path.abspath(args.asset)
    if args.setup:
        setup(asset_dir)
    elif args.apply:
        apply(asset_dir)
    elif args.finalize is not None:
        finalize(asset_dir, args.finalize)
    else:
        status(asset_dir)


if __name__ == "__main__":
    main()
