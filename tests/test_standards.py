"""standards.yaml の読み込みと簡易YAMLパーサのテスト（bpy 不要）。"""
from scripts.lib.standards import _mini_yaml_parse, load_standards


def test_load_standards_has_required_sections():
    std = load_standards()
    for key in ("units", "poly_budget", "mesh_rules", "naming", "export"):
        assert key in std, f"standards.yaml に {key} がない"


def test_poly_budgets_are_positive_ints():
    std = load_standards()
    for name, budget in std["poly_budget"].items():
        assert isinstance(budget, int) and budget > 0, name


def test_mini_parser_nested_and_lists():
    text = """
# comment
a:
  b: 1
  c:
    - x
    - 2
  d: true
e: -1.5
"""
    out = _mini_yaml_parse(text)
    assert out["a"]["b"] == 1
    assert out["a"]["c"] == ["x", 2]
    assert out["a"]["d"] is True
    assert out["e"] == -1.5


def test_mini_parser_matches_standards_schema():
    # 実ファイルを簡易パーサで読んでも構造が壊れないこと
    import os

    path = os.path.join(os.path.dirname(__file__), "..", "config", "standards.yaml")
    with open(path, encoding="utf-8") as f:
        out = _mini_yaml_parse(f.read())
    assert out["poly_budget"]["npc_character"] == 25000
    assert out["export"]["formats"] == ["glb"]
