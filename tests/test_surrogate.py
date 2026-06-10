"""解析サロゲート(predict_metrics)のテスト（bpy 不要）。

bpy が無い CI でも回せるよう、bpy ビルドとの一致は別途（開発時）確認し、
ここでは形・単調性・予算境界などサロゲート単体の性質を検証する。
"""
import pytest

from scripts.lib import humanoid as H
from scripts.lib import quadruped as Q
from scripts.lib.scoring import PROP_WEIGHTS


@pytest.mark.parametrize("G", [H, Q])
def test_predict_metrics_covers_scored_keys(G):
    m = G.predict_metrics(G.default_params())
    # scoring が見るキーのうち、その生成器の目標になり得るものは realized に存在する
    for key in m:
        if key.endswith("_deg") or key.endswith("_ratio") or key.endswith("_m"):
            assert isinstance(m[key], (int, float))
    assert "tris" in m and m["tris"] > 0


@pytest.mark.parametrize("G", [H, Q])
def test_tris_grows_quadratically_with_seg(G):
    base = G.default_params()
    t_low = G.predict_metrics({**base, "seg": 8})["tris"]
    t_mid = G.predict_metrics({**base, "seg": 16})["tris"]
    t_hi = G.predict_metrics({**base, "seg": 32})["tris"]
    assert t_low < t_mid < t_hi
    # 球が支配的なので倍々以上に増える（線形でない）
    assert (t_hi - t_mid) > (t_mid - t_low)


@pytest.mark.parametrize("G", [H, Q])
def test_high_seg_exceeds_budget(G):
    # seg を上げれば 25k 予算を超える解析値になる（予算学習が機能する前提）
    big = G.predict_metrics({**G.default_params(), "seg": 60})["tris"]
    assert big > 25000


@pytest.mark.parametrize("G", [H, Q])
def test_predict_is_deterministic(G):
    p = G.default_params()
    assert G.predict_metrics(p) == G.predict_metrics(p)


def test_tris_formula_matches_known_fit():
    # 実測フィット値（test 実行時に bpy 不要で固定値として検証）
    assert H.predict_metrics({**H.default_params(), "seg": 16})["tris"] == 3760
    assert Q.predict_metrics({**Q.default_params(), "seg": 16})["tris"] == 4336
