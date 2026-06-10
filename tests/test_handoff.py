"""引き継ぎ文書ビルダーのテスト（bpy 不要）。"""
import json

from scripts.handoff.build_handoff import _sculpt_hints, build_handoff_doc


def _make_asset(tmp_path, generator="quadruped"):
    (tmp_path / "learn").mkdir(parents=True)
    (tmp_path / "references").mkdir()
    (tmp_path / "asset.yaml").write_text(
        f"name: t\ndisplay_name: \"Test\"\ntype: npc_character\n"
        f"generator: {generator}\nspecies: quadruped_canine\n", encoding="utf-8")
    (tmp_path / "learn" / "working_target.json").write_text(
        json.dumps({"body_length_m": 1.4000000000000001, "stifle_deg": 35}),
        encoding="utf-8")
    (tmp_path / "learn" / "critique_history.jsonl").write_text(
        json.dumps({"round": 1, "overall": 6.0, "passed": False, "summary": "x"}) + "\n" +
        json.dumps({"round": 2, "overall": 9.0, "passed": True, "summary": "合格"}) + "\n",
        encoding="utf-8")
    (tmp_path / "references" / "sources.json").write_text(
        json.dumps({"sources": [{"id": "s1", "title": "Study", "url": "http://x",
                                 "license_note": "閲覧のみ"}]}), encoding="utf-8")


def test_doc_includes_spec_and_pass_round(tmp_path):
    _make_asset(tmp_path)
    doc = build_handoff_doc(str(tmp_path))
    assert "# 引き継ぎ: Test" in doc
    assert "合格: ラウンド 2 / スコア 9.0" in doc
    assert "5.7" not in doc  # 他アセットの値が混ざらない
    assert "6.0 → 9.0" in doc


def test_float_noise_is_rounded(tmp_path):
    _make_asset(tmp_path)
    doc = build_handoff_doc(str(tmp_path))
    assert "1.4000000000000001" not in doc
    assert "body_length_m: 1.4" in doc


def test_references_listed_without_media(tmp_path):
    _make_asset(tmp_path)
    doc = build_handoff_doc(str(tmp_path))
    assert "[Study](http://x)" in doc
    assert "閲覧のみ" in doc


def test_sculpt_hints_vary_by_generator():
    quad = _sculpt_hints({"generator": "quadruped"})
    humanoid = _sculpt_hints({"generator": "humanoid"})
    assert any("吻" in h for h in quad)
    assert any("指" in h for h in humanoid)
    assert quad != humanoid
