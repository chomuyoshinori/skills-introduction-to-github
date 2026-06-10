"""採点ロジックのテスト（bpy 不要）。"""
from scripts.lib.scoring import proportion_error, score_attempt

TARGET = {"height_m": 1.3, "head_ratio": 0.26, "knee_bend_deg": 20}


def test_perfect_match_has_zero_error():
    realized = dict(TARGET)
    assert proportion_error(realized, TARGET) == 0.0


def test_angle_keys_use_fixed_denominator():
    # 目標 0° の角度でも誤差が発散しない
    target = {"knee_bend_deg": 0}
    err = proportion_error({"knee_bend_deg": 45}, target)
    assert 0 < err < 1


def test_valid_attempt_scored_from_100():
    realized = dict(TARGET)
    valid = {"ok": True, "fail_kinds": set(), "tris": 250}
    sc = score_attempt(realized, TARGET, valid, budget=25000)
    assert sc["valid"] and 99 <= sc["score"] <= 100


def test_invalid_attempt_gets_negative_score():
    valid = {"ok": False, "fail_kinds": {"anatomy", "budget"}, "tris": None}
    sc = score_attempt({}, TARGET, valid, budget=25000)
    assert not sc["valid"] and sc["score"] < 0
    assert sorted(sc["fail_kinds"]) == ["anatomy", "budget"]


def test_poly_penalty_prefers_lighter_mesh():
    realized = dict(TARGET)
    light = score_attempt(realized, TARGET, {"ok": True, "fail_kinds": set(), "tris": 100}, 25000)
    heavy = score_attempt(realized, TARGET, {"ok": True, "fail_kinds": set(), "tris": 24000}, 25000)
    assert light["score"] > heavy["score"]
