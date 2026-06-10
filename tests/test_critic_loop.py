"""critic ループの目標更新ロジックのテスト（bpy 不要）。"""
import json

from scripts.learn.critic_loop import _weighted_overall


def test_weighted_overall_uses_only_present_dimensions():
    rubric = {"silhouette": 0.25, "proportion": 0.20, "pose_naturalness": 0.20,
              "anatomy_plausibility": 0.15, "game_fit": 0.20}
    scores = {"silhouette": 8, "proportion": 9, "pose_naturalness": 8,
              "anatomy_plausibility": 8, "game_fit": 8}
    # 0.25*8+0.2*9+0.2*8+0.15*8+0.2*8 = 8.2
    assert _weighted_overall(scores, rubric) == 8.2


def test_weighted_overall_renormalizes_missing_dimensions():
    rubric = {"a": 0.5, "b": 0.5}
    # b が欠けていても a だけで正規化される
    assert _weighted_overall({"a": 7}, rubric) == 7.0


def test_directive_application_clamps_to_generator_bounds(tmp_path, monkeypatch):
    # apply のクランプ挙動を humanoid の clamp_params 経由で検証
    from scripts.lib import humanoid as G

    target = {"leg_ratio": 0.35}
    # 定義域 (0.34, 0.50) を下回る指示はクランプされる
    target["leg_ratio"] = target["leg_ratio"] - 0.10
    clamped = G.clamp_params(target)
    assert clamped["leg_ratio"] == 0.34


def test_critique_history_roundtrip(tmp_path):
    # 履歴レコードが JSONL として読み書きできる
    rec = {"round": 1, "overall": 6.3, "passed": False, "summary": "x", "scores": {}}
    p = tmp_path / "h.jsonl"
    with open(p, "w") as f:
        f.write(json.dumps(rec) + "\n")
    with open(p) as f:
        back = json.loads(f.readline())
    assert back["overall"] == 6.3 and back["passed"] is False
