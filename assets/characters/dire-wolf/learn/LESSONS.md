# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 1302 / 成功: 1236 / 失敗: 66
- 失敗の内訳: anatomy:50, budget:8, scale:8

## 失敗から学んだ制約
- **seg < 35**: これ以上はポリゴン予算を超過した
- **height ≥ 0.56m**: これ未満はスケール検査に落ちた
- **height ≤ 1.66m**: これ超はスケール検査に落ちた
- **19.9 < elbow_deg < 150.5**: 可動域違反から学習した実行可能レンジ
- **-30.0 < hip_pitch_deg < 111.6**: 可動域違反から学習した実行可能レンジ
- **29.7 < hock_deg < 140.0**: 可動域違反から学習した実行可能レンジ
- **-20.0 < neck_pitch_deg < 30.2**: 可動域違反から学習した実行可能レンジ
- **-40.0 < shoulder_pitch_deg < 162.3**: 可動域違反から学習した実行可能レンジ
- **19.9 < stifle_deg < 130.1**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- body_length_m: 1.2677
- head_ratio: 0.2175
- neck_ratio: 0.3989
- hind_leg_ratio: 0.7264
- front_leg_ratio: 0.5955
- body_radius_ratio: 0.1293
- tail_ratio: 0.2946
- limb_radius: 0.0615
- seg: 14.6
- neck_pitch_deg: -4.8427
- hip_pitch_deg: 21.3938
- stifle_deg: 94.4886
- hock_deg: 65.0408
- shoulder_pitch_deg: -35.034
- elbow_deg: 45.9717
- tail_pitch_deg: -14.3603

## 現在のベスト
- スコア: **74.54**
- params:
  ```json
  {"body_length_m": 1.0856610411494634, "head_ratio": 0.2178297231466258, "neck_ratio": 0.4, "hind_leg_ratio": 0.742327048790375, "front_leg_ratio": 0.6133229732778533, "body_radius_ratio": 0.12759439340546802, "tail_ratio": 0.3036610365026601, "limb_radius": 0.06006798464101783, "seg": 20, "neck_pitch_deg": 4.517616961121351, "hip_pitch_deg": 26.45637991389821, "stifle_deg": 95.77218274022715, "hock_deg": 69.19683460400023, "shoulder_pitch_deg": -31.170040165343284, "elbow_deg": 49.013198799796555, "tail_pitch_deg": -3.862105717650042}
  ```
