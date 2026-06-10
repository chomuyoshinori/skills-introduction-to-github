# Character & Prop Studio — プロジェクト記憶

> 次のセッションはまずこれを読むこと。このプロジェクトで「学んだこと」の入口。
> 詳細は `docs/pipeline.md` / `docs/learning.md` / `docs/security.md`、
> 知見の生データは各アセットの `learn/lessons.json` と `learn/critique_history.jsonl`。

## これは何か
Blender(bpy) + AI で、キャラクター/ゲーム小物の**ブロッキング（プロポーション・ポーズ）を
自動で作り込む**システム。スカルプト等の創造的仕上げは人＋専門エージェントへ引き継ぐ。

## 最重要の教訓（毎回これに立ち返る）
1. **精度向上の主戦場は「目標値の微調整」ではなく「評価系・生成器の修理」**。
   9.0 を超える伸びは、(a) 生成器の表現力の天井を上げる（耳/吻/手足/肉球）か、
   (b) 計測の穴＝報酬ハッキングを塞ぐ（背線の水平さ・キ甲高・前後肢の踏み込み位置を
   採点に追加）ことで生まれた。パラメータをいじるだけでは頭打ちになる。
2. **批評家(critic)は厳しく保つ**。8.5〜8.9 で何ラウンドも合格させないことで、
   安易な収束でなく本質的改善（道具の進化）に追い込めた。
3. **最適化器は必ず抜け道を見つける**。脚を縮め樽胴で身長を稼ぐ等。検査・採点に
   穴があれば必ず突かれる前提で評価系を設計する。
4. **目標は自己矛盾し得る**。見た目の推測でなく数値監査を。例: 脚比率が暗黙に意味する
   肩高と明示目標が矛盾 → 「後肢が短い」の真因は「前肢が長い」だった。

## アーキテクチャ（どこに何があるか）
- `scripts/lib/humanoid.py` / `quadruped.py` … パラメトリック生成器。
  **`predict_metrics()` は bpy 非依存の解析メトリクス**で、`build()`（bpy で実メッシュ）と
  数値が一致する（tris まで実測フィット）。探索はサロゲートで回し、bpy は候補/確定時のみ。
- `scripts/learn/optimizer.py` … 試行錯誤の探索（**bpy 不要・~300試行/秒**）。
- `scripts/learn/critic_loop.py` … actor-critic ループ。`--setup`→AIが `critique.json`→`--apply`→…→`--finalize`。
- `scripts/learn/reference.py` … web実測値を目標に接地（出典のみ保存、画像は保存しない）。
- `scripts/learn/lessons.py` … 知識ベース（可動域・予算境界・sweet spot）。アトミック保存。
- `scripts/handoff/build_handoff.py` … 仕上げ工程への引き継ぎ一式を生成。
- `config/standards.yaml`（規格）/ `config/anatomy.yaml`（関節可動域）。

## 守るべき不変条件（壊すと検査に落ちる）
- 生成メッシュは常に**多様体・Ngonなし・UVあり**（円柱フタは TRIFAN、面は三角/四角のみ）。
- pip 版 bpy では **`import bpy` を bmesh/mathutils より先に**。
- `.blend` は必ず `scripts/lib/blendio.open_blend`（スクリプト自動実行を無効化）で開く。
- 生成器を変えたら **`predict_metrics` の tris 式も合わせる**（`tests/test_surrogate.py` が検知）。

## 現在の到達点
- goblin-warrior（人型, npc）: critic **9.5** 合格・確定済み。
- dire-wolf（四足・イヌ科, npc）: critic **9.5** 合格・確定済み。
- テスト 40 件・`scripts/checks/validate_assets.py`・`compileall` が緑。

## 再開コマンド
```bash
pip install bpy                     # 環境に bpy が無ければ
python -m pytest tests/ -q          # 健全性確認（bpy 不要）
# 新アセット: assets/characters/_template をコピー → asset.yaml 編集 → challenge.yaml 作成
python scripts/learn/critic_loop.py --asset <asset> --setup   # 1ラウンド（最適化+候補描画）
#   → AI が agents/critic.md の役割で learn/critique.json を採点
python scripts/learn/critic_loop.py --asset <asset> --apply   # 反映
python scripts/learn/critic_loop.py --asset <asset> --finalize <候補番号>  # 確定
```

## 次にやるなら
- 新しい生体（鳥型・人型ヒーロー）へ同枠組みを展開（生成器を1つ足すだけ）。
- 仕上げ工程：`HANDOFF.md` を人＋ `agents/modeler.md` 等へ。
- 視覚レビューの全自動化（Claude API で critic 採点を無人実行）。
