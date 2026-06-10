# 引き継ぎ: Dire Wolf

> このファイルは scripts/handoff/build_handoff.py が自動生成します。
> ブロッキングは検証・合格済みです。ここから先の造形は人＋専門エージェントが担当します。

## 成果物
- `export/` … 検証済みの最終ブロッキング（glb）
- `highpoly/base.blend` … リグ(ROM制約)付きの .blend
- `highpoly/turnaround_{front,right,back,left}.png` … 4方向ビュー

## 仕様（達成済みプロポーション/ポーズ）
- 種別: `npc_character` / ポリゴン予算: 25000 tris
- 目標値（参照接地＋critic調整の最終形）:
  - height_m: 1.1
  - body_length_m: 1.4
  - head_ratio: 0.2
  - neck_ratio: 0.4
  - hind_leg_ratio: 0.73
  - front_leg_ratio: 0.59
  - tail_ratio: 0.57
  - neck_pitch_deg: 10
  - hip_pitch_deg: 15.0
  - stifle_deg: 80.0
  - hock_deg: 66.0
  - shoulder_pitch_deg: -25
  - elbow_deg: 35
  - body_radius_ratio: 0.125
  - limb_radius: 0.08
  - tail_pitch_deg: -35
  - back_slope_deg: 0
  - shoulder_height_m: 0.78
  - hind_reach_ratio: 0.12
  - front_reach_ratio: 0.02

## 品質の達成経緯
- **合格: ラウンド 17 / スコア 9.0**
- 反復ラウンド数: 19
- スコア推移: 5.7 → 4.85 → 5.95 → 5.8 → 5.15 → 4.93 → 5.47 → 5.97 → 5.88 → 6.9 → 7.53 → 8.02 → 8.53 → 8.82 → 7.92 → 8.9 → 9.0 → 9.3 → 9.5

批評家の最終評価:
> 課題達成。最良案(1)は立ち耳・長い吻・水平な背・深い胸・絞れた腰・四肢の支柱・後肢の正しい3節屈曲・垂れ尾が全て成立し、後肢も胴の真下に踏み込んで四つ脚で安定。17ラウンドで指摘した全欠点（犬体型/短足/細さ/尾向き/背の傾き/キ甲高ごまかし/目標矛盾/玉頭・耳なし/後肢後流れ）を解消。獣医解剖学の実測に接地した、出荷可能なオオカミのブロッキング。仕上げ(毛・指・表情)は人＋専門エージェントへ。

## スカルプト指示書（次の担当へ）
ブロッキングはプロポーションとポーズの土台です。次の工程で作り込んでください:

1. **リトポ前のディテール（highpoly）**
   - 関節球は造形の当たり。実際の筋・腱の流れに沿って繋ぐ
   - シルエットを壊さない範囲で面取り・肉付け
2. **造形の要点**（critic が重視した点を引き継ぐ）
   - 頭部: 立ち耳の薄さと吻の長さがイヌ科の生命線。丸めすぎない
   - 胴: 深い胸と絞れた腰のラインを強調し、肋骨の張りを出す
   - 四肢: 後肢の stifle/hock の二段の折れを筋肉で繋ぎ、肉球で接地
   - 尾: 付け根を太く先を房状に。毛流れで動きを出す
3. **リグ**: `base.blend` のボーンには可動域(Limit Rotation)が焼き込み済み。これを尊重したウェイト付けを行う（`config/anatomy.yaml` 参照）
4. **検査**: 仕上げ後も `scripts/checks/validate_mesh.py` を通すこと

担当エージェント: `agents/modeler.md`（造形レビュー）/ `agents/retopo-uv.md`（リトポ）/ `agents/texture-artist.md`（質感）

## 参照（出典のみ・メディアは未保存）
- [Determination of the Stifle Angle at Standing Position in Dogs (Vet Sci, 2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9697634/) — 閲覧のみ。実測の関節角(事実)のみ利用。本文/図は保存しない。
- [Axes and angles in canine orthopedics (IMAIOS vet-anatomy)](https://www.imaios.com/en/vet-anatomy/dog/dog-axes-and-angles) — 閲覧のみ。角度の数値のみ利用。
- [Structure and Movement Pt 1 (Breeding Better Dogs)](https://breedingbetterdogs.com/article/structure-and-movement-pt-1) — 閲覧のみ。立位の角度づけの記述のみ参考。

