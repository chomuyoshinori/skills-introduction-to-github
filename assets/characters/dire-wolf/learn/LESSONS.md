# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 152 / 成功: 111 / 失敗: 41
- 失敗の内訳: anatomy:31, budget:7, scale:3

## 失敗から学んだ制約
- **seg < 37**: これ以上はポリゴン予算を超過した
- **height ≥ 0.55m**: これ未満はスケール検査に落ちた
- **height ≤ 2.14m**: これ超はスケール検査に落ちた
- **19.8 < elbow_deg < 150.8**: 可動域違反から学習した実行可能レンジ
- **-31.8 < hip_pitch_deg < 111.6**: 可動域違反から学習した実行可能レンジ
- **29.6 < hock_deg < 140.1**: 可動域違反から学習した実行可能レンジ
- **-20.8 < neck_pitch_deg < 31.6**: 可動域違反から学習した実行可能レンジ
- **-40.1 < shoulder_pitch_deg < 162.3**: 可動域違反から学習した実行可能レンジ
- **18.9 < stifle_deg < 130.1**: 可動域違反から学習した実行可能レンジ

## 成功から学んだ良パラメータ域 (sweet spot)
- body_length_m: 1.1782
- head_ratio: 0.173
- neck_ratio: 0.2688
- hind_leg_ratio: 0.6911
- front_leg_ratio: 0.4759
- body_radius_ratio: 0.1185
- tail_ratio: 0.402
- limb_radius: 0.08
- seg: 9.4
- neck_pitch_deg: -11.9191
- hip_pitch_deg: 10.8841
- stifle_deg: 79.5589
- hock_deg: 56.9238
- shoulder_pitch_deg: -27.7579
- elbow_deg: 29.5644

## 現在のベスト
- スコア: **97.46**
- params:
  ```json
  {"body_length_m": 1.0479008140451096, "head_ratio": 0.16561700885296485, "neck_ratio": 0.26465344865896934, "hind_leg_ratio": 0.7252070092214681, "front_leg_ratio": 0.47820844366956633, "body_radius_ratio": 0.13303068873229684, "tail_ratio": 0.3857754851882254, "limb_radius": 0.08, "seg": 6, "neck_pitch_deg": -8.797888917109486, "hip_pitch_deg": 23.901734971886395, "stifle_deg": 92.40012253806763, "hock_deg": 64.86621382779546, "shoulder_pitch_deg": -15.11878186240479, "elbow_deg": 29.966808975099518}
  ```
