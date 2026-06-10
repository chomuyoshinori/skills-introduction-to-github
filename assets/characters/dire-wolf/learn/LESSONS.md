# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 192 / 成功: 147 / 失敗: 45
- 失敗の内訳: anatomy:34, budget:7, scale:4

## 失敗から学んだ制約
- **seg < 37**: これ以上はポリゴン予算を超過した
- **height ≥ 0.55m**: これ未満はスケール検査に落ちた
- **height ≤ 1.81m**: これ超はスケール検査に落ちた
- **19.8 < elbow_deg < 150.8**: 可動域違反から学習した実行可能レンジ
- **-30.9 < hip_pitch_deg < 111.6**: 可動域違反から学習した実行可能レンジ
- **29.6 < hock_deg < 140.1**: 可動域違反から学習した実行可能レンジ
- **-20.8 < neck_pitch_deg < 30.2**: 可動域違反から学習した実行可能レンジ
- **-40.1 < shoulder_pitch_deg < 162.3**: 可動域違反から学習した実行可能レンジ
- **18.9 < stifle_deg < 130.1**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- body_length_m: 1.3658
- head_ratio: 0.2644
- neck_ratio: 0.2847
- hind_leg_ratio: 0.3804
- front_leg_ratio: 0.5793
- body_radius_ratio: 0.1835
- tail_ratio: 0.3207
- limb_radius: 0.074
- seg: 7.2
- neck_pitch_deg: 2.3483
- hip_pitch_deg: 17.3719
- stifle_deg: 52.0033
- hock_deg: 40.9117
- shoulder_pitch_deg: 51.4076
- elbow_deg: 24.3623

## 現在のベスト
- スコア: **74.58**
- params:
  ```json
  {"body_length_m": 1.2825058682110904, "head_ratio": 0.2551187400583184, "neck_ratio": 0.3002743108935832, "hind_leg_ratio": 0.36231276800485757, "front_leg_ratio": 0.5861929691479639, "body_radius_ratio": 0.18241632056161963, "tail_ratio": 0.29513660538964603, "limb_radius": 0.07315430638844246, "seg": 6, "neck_pitch_deg": 5.234325426273128, "hip_pitch_deg": 21.720681784129344, "stifle_deg": 42.47990117246346, "hock_deg": 33.6, "shoulder_pitch_deg": 47.3239494151686, "elbow_deg": 26.611387933492843}
  ```
