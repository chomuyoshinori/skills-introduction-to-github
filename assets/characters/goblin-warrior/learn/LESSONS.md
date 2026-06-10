# 学習済み知見 (LESSONS)

> このファイルは scripts/learn/optimizer.py が自動生成します。

## 統計
- 総試行: 60 / 成功: 59 / 失敗: 1
- 失敗の内訳: budget:1

## 失敗から学んだ制約
- **seg < 165**: これ以上はポリゴン予算を超過した

## 成功から学んだ良パラメータ域 (sweet spot)
- height_m: 1.3382
- head_ratio: 0.2904
- torso_ratio: 0.3434
- leg_ratio: 0.3811
- arm_ratio: 0.3038
- shoulder_w: 0.1922
- limb_radius: 0.0944
- lean_deg: 10.3572
- seg: 12.4

## 現在のベスト
- スコア: **90.06**
- params:
  ```json
  {"height_m": 1.2694141191998836, "head_ratio": 0.298690527885296, "torso_ratio": 0.3436887037834886, "leg_ratio": 0.3851284330806518, "arm_ratio": 0.3, "shoulder_w": 0.18078167539706616, "limb_radius": 0.09615375030066015, "lean_deg": 11.327968946952332, "seg": 9}
  ```
