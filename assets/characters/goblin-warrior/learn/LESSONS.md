# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 1943 / 成功: 1886 / 失敗: 57
- 失敗の内訳: anatomy:39, budget:3, scale:15

## 失敗から学んだ制約
- **seg < 40**: これ以上はポリゴン予算を超過した
- **height ≥ 0.64m**: これ未満はスケール検査に落ちた
- **height ≤ 2.69m**: これ超はスケール検査に落ちた
- **-0.4 < elbow_bend_deg < 145.8**: 可動域違反から学習した実行可能レンジ
- **-20.0 < hip_pitch_deg < 120.1**: 可動域違反から学習した実行可能レンジ
- **-0.0 < knee_bend_deg < 150.6**: 可動域違反から学習した実行可能レンジ
- **-30.1 < lean_deg < 45.0**: 可動域違反から学習した実行可能レンジ
- **-60.3 < shoulder_pitch_deg < 180.2**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- height_m: 1.1746
- head_ratio: 0.2798
- torso_ratio: 0.3722
- leg_ratio: 0.4422
- arm_ratio: 0.4059
- shoulder_w: 0.228
- limb_radius: 0.1023
- seg: 6.4
- lean_deg: 30.0484
- hip_pitch_deg: 0.2743
- knee_bend_deg: 18.7539
- shoulder_pitch_deg: 21.4212
- elbow_bend_deg: 52.9888

## 現在のベスト
- スコア: **87.39**
- params:
  ```json
  {"height_m": 1.3017714873136754, "head_ratio": 0.2681369478844736, "torso_ratio": 0.36287575209879225, "leg_ratio": 0.46071264339920587, "arm_ratio": 0.4087298692043792, "shoulder_w": 0.23325558337039956, "limb_radius": 0.10619979806770728, "seg": 6, "lean_deg": 41.0, "hip_pitch_deg": 10.870286213589852, "knee_bend_deg": 25.915113629848754, "shoulder_pitch_deg": 10.096369233255126, "elbow_bend_deg": 57.947480738568046}
  ```
