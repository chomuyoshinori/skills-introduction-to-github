# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 652 / 成功: 599 / 失敗: 53
- 失敗の内訳: anatomy:42, budget:7, scale:4

## 失敗から学んだ制約
- **seg < 37**: これ以上はポリゴン予算を超過した
- **height ≥ 0.55m**: これ未満はスケール検査に落ちた
- **height ≤ 1.81m**: これ超はスケール検査に落ちた
- **19.8 < elbow_deg < 150.5**: 可動域違反から学習した実行可能レンジ
- **-30.2 < hip_pitch_deg < 111.6**: 可動域違反から学習した実行可能レンジ
- **29.6 < hock_deg < 140.1**: 可動域違反から学習した実行可能レンジ
- **-20.1 < neck_pitch_deg < 30.2**: 可動域違反から学習した実行可能レンジ
- **-40.0 < shoulder_pitch_deg < 162.3**: 可動域違反から学習した実行可能レンジ
- **19.6 < stifle_deg < 130.1**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- body_length_m: 1.153
- head_ratio: 0.1935
- neck_ratio: 0.3286
- hind_leg_ratio: 0.5556
- front_leg_ratio: 0.6204
- body_radius_ratio: 0.1493
- tail_ratio: 0.2437
- limb_radius: 0.0438
- seg: 17.2
- neck_pitch_deg: -0.1585
- hip_pitch_deg: 36.0605
- stifle_deg: 84.0351
- hock_deg: 79.4837
- shoulder_pitch_deg: -30.5365
- elbow_deg: 48.7849
- tail_pitch_deg: -39.452

## 現在のベスト
- スコア: **71.91**
- params:
  ```json
  {"body_length_m": 1.1269650731362404, "head_ratio": 0.18335208437962394, "neck_ratio": 0.30753788789403547, "hind_leg_ratio": 0.5255256111674111, "front_leg_ratio": 0.6519427512121866, "body_radius_ratio": 0.14937922376269824, "tail_ratio": 0.26132567757324243, "limb_radius": 0.04393895670475915, "seg": 19, "neck_pitch_deg": -0.3740662851878893, "hip_pitch_deg": 34.04010274794496, "stifle_deg": 80.9267585836175, "hock_deg": 70.82266860325727, "shoulder_pitch_deg": -36.0, "elbow_deg": 43.43765561882496, "tail_pitch_deg": -43.45356058343067}
  ```
