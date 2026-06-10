# 引き継ぎ: Goblin Warrior

> このファイルは scripts/handoff/build_handoff.py が自動生成します。
> ブロッキングは検証・合格済みです。ここから先の造形は人＋専門エージェントが担当します。

## 成果物
- `export/` … 検証済みの最終ブロッキング（glb）
- `highpoly/base.blend` … リグ(ROM制約)付きの .blend
- `highpoly/turnaround_{front,right,back,left}.png` … 4方向ビュー

## 仕様（達成済みプロポーション/ポーズ）
- 種別: `npc_character` / ポリゴン予算: 25000 tris
- 目標値（参照接地＋critic調整の最終形）:
  - height_m: 1.3
  - head_ratio: 0.27
  - torso_ratio: 0.38
  - leg_ratio: 0.35
  - arm_ratio: 0.42
  - shoulder_w: 0.26
  - lean_deg: 21.0
  - hip_pitch_deg: 12.0
  - knee_bend_deg: 22.0
  - shoulder_pitch_deg: 28.0
  - elbow_bend_deg: 63.0
  - limb_radius: 0.105

## 品質の達成経緯
- **合格: ラウンド 4 / スコア 8.2**
- 反復ラウンド数: 8
- スコア推移: 6.3 → 5.25 → 7.8 → 8.2 → 8.4 → 8.83 → 9.12 → 9.5

批評家の最終評価:
> 課題到達。寸胴・大頭・太い四肢・広い肩で、前傾の安定した低い構え。遠目にも『小柄で俊敏なゴブリン戦士』と明確に読め、左右対称で接地も安定、ポリゴンも予算内。出荷可能な水準のブロッキング。仕上げ（顔・装備・スカルプト）は人＋専門エージェントへ引き継ぐ。

## スカルプト指示書（次の担当へ）
ブロッキングはプロポーションとポーズの土台です。次の工程で作り込んでください:

1. **リトポ前のディテール（highpoly）**
   - 関節球は造形の当たり。実際の筋・腱の流れに沿って繋ぐ
   - シルエットを壊さない範囲で面取り・肉付け
2. **造形の要点**（critic が重視した点を引き継ぐ）
   - 頭部: 大きめの頭のキャラ性を活かしつつ、顔のディテールを作る
   - 胴: 量感（嵩）を保ったまま筋肉のメリハリを付ける
   - 四肢: 関節球を当たりに、肘・膝の方向を明確に
   - 手足: ブロッキングには無い指を追加する
3. **リグ**: `base.blend` のボーンには可動域(Limit Rotation)が焼き込み済み。これを尊重したウェイト付けを行う（`config/anatomy.yaml` 参照）
4. **検査**: 仕上げ後も `scripts/checks/validate_mesh.py` を通すこと

担当エージェント: `agents/modeler.md`（造形レビュー）/ `agents/retopo-uv.md`（リトポ）/ `agents/texture-artist.md`（質感）

