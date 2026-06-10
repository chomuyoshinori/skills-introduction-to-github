# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 343 / 成功: 299 / 失敗: 44
- 失敗の内訳: anatomy:30, budget:3, scale:11

## 失敗から学んだ制約
- **seg < 40**: これ以上はポリゴン予算を超過した
- **height ≥ 0.25m**: これ未満はスケール検査に落ちた
- **height ≤ 2.74m**: これ超はスケール検査に落ちた
- **-0.4 < elbow_bend_deg < 145.8**: 可動域違反から学習した実行可能レンジ
- **-20.1 < hip_pitch_deg < 121.6**: 可動域違反から学習した実行可能レンジ
- **-0.1 < knee_bend_deg < 150.6**: 可動域違反から学習した実行可能レンジ
- **-30.1 < lean_deg < 45.2**: 可動域違反から学習した実行可能レンジ
- **-60.3 < shoulder_pitch_deg < 180.8**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- height_m: 1.0954
- head_ratio: 0.2979
- torso_ratio: 0.3392
- leg_ratio: 0.3699
- arm_ratio: 0.3555
- shoulder_w: 0.2013
- limb_radius: 0.0457
- seg: 27.4
- lean_deg: -23.9403
- hip_pitch_deg: -3.6936
- knee_bend_deg: 26.4622
- shoulder_pitch_deg: 8.4525
- elbow_bend_deg: 41.8916

## 現在のベスト
- スコア: **71.2**
- params:
  ```json
  {"height_m": 1.4225798409890344, "head_ratio": 0.2995975081196165, "torso_ratio": 0.33591095249161584, "leg_ratio": 0.37217221563115405, "arm_ratio": 0.352344812134147, "shoulder_w": 0.19764639521707472, "limb_radius": 0.044193735661843155, "seg": 34, "lean_deg": -23.502449673326883, "hip_pitch_deg": 0.9453817069305934, "knee_bend_deg": 3.9, "shoulder_pitch_deg": 4.611259048471032, "elbow_bend_deg": 45.1674056724544}
  ```
