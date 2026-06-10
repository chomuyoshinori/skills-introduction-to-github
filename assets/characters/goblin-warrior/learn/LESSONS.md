# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 200 / 成功: 165 / 失敗: 35
- 失敗の内訳: anatomy:23, budget:3, scale:9

## 失敗から学んだ制約
- **seg < 40**: これ以上はポリゴン予算を超過した
- **height ≥ 0.25m**: これ未満はスケール検査に落ちた
- **height ≤ 2.84m**: これ超はスケール検査に落ちた
- **-0.4 < elbow_bend_deg < 146.7**: 可動域違反から学習した実行可能レンジ
- **-20.1 < hip_pitch_deg < 123.2**: 可動域違反から学習した実行可能レンジ
- **-0.7 < knee_bend_deg < 150.6**: 可動域違反から学習した実行可能レンジ
- **-30.1 < lean_deg < 45.2**: 可動域違反から学習した実行可能レンジ
- **-60.3 < shoulder_pitch_deg < 201.0**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- height_m: 1.245
- head_ratio: 0.2361
- torso_ratio: 0.3427
- leg_ratio: 0.3488
- arm_ratio: 0.4502
- shoulder_w: 0.276
- limb_radius: 0.0529
- seg: 7.2
- lean_deg: 0.8976
- hip_pitch_deg: 4.5654
- knee_bend_deg: 27.9215
- shoulder_pitch_deg: 26.5963
- elbow_bend_deg: 51.5431

## 現在のベスト
- スコア: **85.8**
- params:
  ```json
  {"height_m": 1.3295662613286043, "head_ratio": 0.2222467867812631, "torso_ratio": 0.34223912006695784, "leg_ratio": 0.3480397554000421, "arm_ratio": 0.44528493921160506, "shoulder_w": 0.2863688909322014, "limb_radius": 0.05992316034432514, "seg": 6, "lean_deg": 5.338473135887878, "hip_pitch_deg": -3.2761160032098324, "knee_bend_deg": 27.77263068458385, "shoulder_pitch_deg": 32.941607065212324, "elbow_bend_deg": 45.75156697900606}
  ```
