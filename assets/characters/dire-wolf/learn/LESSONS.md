# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 2102 / 成功: 2025 / 失敗: 77
- 失敗の内訳: anatomy:55, budget:8, scale:14

## 失敗から学んだ制約
- **seg < 35**: これ以上はポリゴン予算を超過した
- **height ≥ 1.04m**: これ未満はスケール検査に落ちた
- **height ≤ 1.66m**: これ超はスケール検査に落ちた
- **19.9 < elbow_deg < 150.5**: 可動域違反から学習した実行可能レンジ
- **-30.0 < hip_pitch_deg < 111.4**: 可動域違反から学習した実行可能レンジ
- **30.0 < hock_deg < 140.0**: 可動域違反から学習した実行可能レンジ
- **-20.0 < neck_pitch_deg < 30.1**: 可動域違反から学習した実行可能レンジ
- **-40.0 < shoulder_pitch_deg < 161.7**: 可動域違反から学習した実行可能レンジ
- **19.9 < stifle_deg < 130.1**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- body_length_m: 1.2341
- head_ratio: 0.1881
- neck_ratio: 0.37
- hind_leg_ratio: 0.7444
- front_leg_ratio: 0.6392
- body_radius_ratio: 0.1245
- tail_ratio: 0.3354
- limb_radius: 0.0524
- seg: 20.2
- neck_pitch_deg: 7.495
- hip_pitch_deg: 15.1166
- stifle_deg: 76.7781
- hock_deg: 56.3129
- shoulder_pitch_deg: -21.6938
- elbow_deg: 37.0614
- tail_pitch_deg: 5.3192

## 現在のベスト
- スコア: **69.46**
- params:
  ```json
  {"body_length_m": 1.2245926197068633, "head_ratio": 0.18750425446843366, "neck_ratio": 0.3741811228926295, "hind_leg_ratio": 0.7431674884270973, "front_leg_ratio": 0.6362921233148978, "body_radius_ratio": 0.12565696204142518, "tail_ratio": 0.33999511417071576, "limb_radius": 0.057449158942317044, "seg": 26, "neck_pitch_deg": 2.8832014468313636, "hip_pitch_deg": 17.469346120098137, "stifle_deg": 72.6579734348145, "hock_deg": 62.251416549128024, "shoulder_pitch_deg": -39.93000964451124, "elbow_deg": 33.593911511478524, "tail_pitch_deg": 5.762957265891986}
  ```
