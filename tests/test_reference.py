"""web 参照ヒントの検証・適用ロジックのテスト（bpy 不要）。"""
import json

from scripts.learn.reference import apply, status


def _write(asset_dir, hints, sources=None):
    refdir = asset_dir / "references"
    refdir.mkdir(parents=True, exist_ok=True)
    (refdir / "reference_hints.json").write_text(
        json.dumps(hints, ensure_ascii=False), encoding="utf-8")
    if sources is not None:
        (refdir / "sources.json").write_text(
            json.dumps(sources, ensure_ascii=False), encoding="utf-8")
    (asset_dir / "asset.yaml").write_text(
        "name: t\ntype: npc_character\ngenerator: quadruped\nspecies: quadruped_canine\n",
        encoding="utf-8")
    (asset_dir / "learn").mkdir(exist_ok=True)


def test_apply_writes_reference_target_within_bounds(tmp_path):
    _write(tmp_path, {"subject": "wolf",
                      "params": {"stifle_deg": {"value": 35, "from": ["s1"],
                                                "confidence": "high", "note": "x"}}},
           {"sources": [{"id": "s1", "title": "src", "url": "http://x"}]})
    apply(str(tmp_path))
    rt = json.loads((tmp_path / "learn" / "reference_target.json").read_text())
    assert rt["stifle_deg"] == 35.0


def test_out_of_range_value_is_clamped_and_recorded(tmp_path):
    # quadruped の stifle_deg 定義域は (-10, 170)。999 はクランプされる。
    _write(tmp_path, {"subject": "x",
                      "params": {"stifle_deg": {"value": 999, "from": [],
                                                "confidence": "low", "note": "y"}}})
    apply(str(tmp_path))
    rt = json.loads((tmp_path / "learn" / "reference_target.json").read_text())
    assert rt["stifle_deg"] == 170
    applied = json.loads((tmp_path / "references" / "applied.json").read_text())
    assert applied["params"][0]["clamped"] is True


def test_unknown_param_is_skipped(tmp_path):
    _write(tmp_path, {"subject": "x",
                      "params": {"not_a_param": {"value": 1, "from": [], "confidence": "low"}}})
    apply(str(tmp_path))
    rt = json.loads((tmp_path / "learn" / "reference_target.json").read_text())
    assert rt == {}


def test_provenance_carries_source_titles(tmp_path):
    _write(tmp_path, {"subject": "x",
                      "params": {"hock_deg": {"value": 45, "from": ["s1"],
                                              "confidence": "medium", "note": "n"}}},
           {"sources": [{"id": "s1", "title": "Study A", "url": "http://a"}]})
    apply(str(tmp_path))
    applied = json.loads((tmp_path / "references" / "applied.json").read_text())
    assert applied["params"][0]["source_titles"] == ["Study A"]
