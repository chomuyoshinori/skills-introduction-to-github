"""知識ベース（lessons）の学習・永続化のテスト（bpy 不要）。"""
import json
import os

from scripts.learn import lessons as L

TARGET = {"height_m": 1.3}


def _attempt(params, valid=True, fail_kinds=(), violations=(), score=80.0):
    return {"params": params, "valid": valid, "score": score,
            "fail_kinds": list(fail_kinds), "violations": list(violations),
            "realized": None}


def test_budget_failure_learns_seg_boundary():
    lessons = L.load("/nonexistent/lessons.json")
    L.update(lessons, _attempt({"seg": 50}, valid=True), TARGET)
    L.update(lessons, _attempt({"seg": 180}, valid=False, fail_kinds=["budget"]), TARGET)
    cap = lessons["constraints"]["seg_cap"]
    assert cap is not None and 50 < cap < 180  # 成功上限と失敗下限の間


def test_anatomy_violation_narrows_param_range():
    lessons = L.load("/nonexistent/lessons.json")
    vio = {"param": "knee_bend_deg", "joint": "knee", "value": 165.0,
           "bound": "max", "limit": 150}
    L.update(lessons, _attempt({"knee_bend_deg": 165.0}, valid=False,
                               fail_kinds=["anatomy"], violations=[vio]), TARGET)
    pr = lessons["constraints"]["param_ranges"]["knee_bend_deg"]
    assert pr["hi"] == 165.0

    # 学習済みレンジで提案が事前補正される
    out, applied = L.apply_constraints(lessons, {"knee_bend_deg": 170.0})
    assert out["knee_bend_deg"] < 165.0 and applied


def test_success_updates_top_k_and_sweet_spot():
    lessons = L.load("/nonexistent/lessons.json")
    for s in (70, 90, 80):
        L.update(lessons, _attempt({"seg": 10, "height_m": 1.0 + s / 100}, score=s), TARGET)
    assert lessons["best"]["score"] == 90
    assert [a["score"] for a in lessons["top_k"]] == [90, 80, 70]
    assert "height_m" in lessons["sweet_spot"]


def test_save_is_atomic_and_load_recovers_from_corruption(tmp_path):
    path = str(tmp_path / "lessons.json")
    lessons = L.load(path)
    L.update(lessons, _attempt({"seg": 10}), TARGET)
    L.save(lessons, path)
    assert not os.path.exists(path + ".tmp")  # 一時ファイルが残らない
    assert L.load(path)["stats"]["total"] == 1

    # 破損ファイルは退避され、空の知識ベースで再開できる
    with open(path, "w") as f:
        f.write("{ broken json")
    recovered = L.load(path)
    assert recovered["stats"]["total"] == 0
    assert os.path.exists(path + ".corrupt")


def test_size_constraint_applies_to_quadruped_param():
    lessons = L.load("/nonexistent/lessons.json")
    lessons["constraints"]["height_ceil"] = 2.0
    out, applied = L.apply_constraints(lessons, {"body_length_m": 2.5})
    assert out["body_length_m"] < 2.0 and applied
