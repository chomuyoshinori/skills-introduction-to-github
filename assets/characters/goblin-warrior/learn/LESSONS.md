# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 220 / 成功: 184 / 失敗: 36
- 失敗の内訳: anatomy:24, budget:3, scale:9

## 失敗から学んだ制約
- **seg < 40**: これ以上はポリゴン予算を超過した
- **height ≥ 0.25m**: これ未満はスケール検査に落ちた
- **height ≤ 2.84m**: これ超はスケール検査に落ちた
- **-0.4 < elbow_bend_deg < 146.7**: 可動域違反から学習した実行可能レンジ
- **-20.1 < hip_pitch_deg < 123.2**: 可動域違反から学習した実行可能レンジ
- **-0.1 < knee_bend_deg < 150.6**: 可動域違反から学習した実行可能レンジ
- **-30.1 < lean_deg < 45.2**: 可動域違反から学習した実行可能レンジ
- **-60.3 < shoulder_pitch_deg < 201.0**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- height_m: 1.245
- head_ratio: 0.235
- torso_ratio: 0.338
- leg_ratio: 0.349
- arm_ratio: 0.4451
- shoulder_w: 0.2719
- limb_radius: 0.0525
- seg: 7.2
- lean_deg: 2.4195
- hip_pitch_deg: 14.0424
- knee_bend_deg: 31.196
- shoulder_pitch_deg: 16.7628
- elbow_bend_deg: 49.0041

## 現在のベスト
- スコア: **101.28**
- params:
  ```json
  {"height_m": 1.064277330207052, "head_ratio": 0.2441229302926215, "torso_ratio": 0.33699818036255125, "leg_ratio": 0.34, "arm_ratio": 0.46, "shoulder_w": 0.24318228714071322, "limb_radius": 0.05515722157721957, "seg": 6, "lean_deg": -2.622709231091764, "hip_pitch_deg": 6.990661832818372, "knee_bend_deg": 27.736298587033478, "shoulder_pitch_deg": 15.61515684320472, "elbow_bend_deg": 35.44150456198135}
  ```
