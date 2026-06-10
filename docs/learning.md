# 試行錯誤で学習するモデリング最適化ループ

「成功も失敗も学習して、自動でより良いブロッキングに近づける」仕組みです。
GPU での機械学習(ニューラルネット訓練)ではなく、**永続的な知識ベースを持つ
最適化ループ**として実装しています。軽量で再現可能、CI でも回せます。

## 全体像

```
            ┌──────────────────────────────────────────────┐
            │  lessons.json（永続知識ベース）              │
            │   - 失敗から学んだ制約（seg上限/height範囲）  │
            │   - 成功から学んだ良域(sweet spot)・ベスト     │
            └──────────────────────────────────────────────┘
                  ▲ 更新                       │ 提案を補正
                  │                            ▼
  提案 → [制約で事前補正] → 生成(bpy) → 検査 → 採点 → 記録(attempts.jsonl)
   ▲                                                        │
   └──────────────────── 次の試行へ ◀───────────────────────┘
```

## 構成要素

| ファイル | 役割 |
|----------|------|
| `scripts/lib/humanoid.py` | パラメトリックな**多関節**人体生成器（球＋円柱、Ngon/非多様体を出さない）。ポーズの運動学とROM制約付きリグ生成、**パラメータ定義域**もここ |
| `config/anatomy.yaml` | 関節の解剖学知識ベース（人間/四足動物の関節タイプと可動域） |
| `scripts/lib/anatomy.py` | ポーズの解剖学的妥当性検査 |
| `scripts/lib/scoring.py` | 目標プロポーション(`asset.yaml` の `target`)との誤差＋ポリゴン消費で**採点** |
| `scripts/lib/meshcheck.py` | 検査コア（命名/スケール/マニフォールド/Ngon/UV/ポリ予算）。CLI検査と共用 |
| `scripts/learn/lessons.py` | **知識ベース**。失敗→制約、成功→良域を更新。`LESSONS.md` も自動生成 |
| `scripts/learn/optimizer.py` | **試行錯誤ループ**本体。過去の記録を読み込んで継続学習 |

## 学習のしくみ

### 失敗から学ぶ（制約の獲得）
- **ポリゴン予算超過**: 超過した最小 seg と、収まった最大 seg から、
  実行可能境界を**二分探索的**に推定して安全上限 `seg_cap` を学ぶ。
  以後の提案は生成前に `seg_cap` 以下へ**事前補正**され、無駄な失敗を避ける。
- **スケール検査落ち**: 失敗した height から安全レンジ(floor/ceil)を狭める。
- **解剖学検査落ち（関節可動域）**: 提案側は関節の可動域(ROM)を知らない。
  膝の逆関節や肩の過回転を提案して検査(`scripts/lib/anatomy.py`)に落ちるたび、
  そのパラメータの実行可能レンジ(`param_ranges`)を狭めていく。
  実測では約120試行で **真の解剖学値にほぼ収束**した
  （肘: 学習 -0.9〜146.7° vs 真値 0〜145° / 股関節: -20.1〜123.2° vs -20〜120°）。

### 成功から学ぶ（良域への収束）
- 上位 K 件の成功例の平均を **sweet spot** として保持し、探索をそこへ寄せる。
- ベスト個体の周辺を突然変異（局所探索）しつつ、一定割合で広域探索して
  新しい良域や失敗境界を探る。

### 永続化と継続学習
- 全試行は `assets/<asset>/learn/attempts.jsonl` に1行1試行で追記。
- 知識ベースは `lessons.json`、人間向けサマリは `LESSONS.md`。
- **再実行すると過去の記録/知見を読み込んで続きから学習**する。

## 使い方

```bash
# 目標は asset.yaml の target: ブロックで定義
python scripts/learn/optimizer.py -- \
    --asset assets/characters/goblin-warrior --iters 60 --seed 3
```

実行すると各試行の合否・スコアが流れ、最後にベストを
`highpoly/base.blend` として保存します。

```bash
# ベストを検査・レンダリングして確認
python scripts/checks/validate_mesh.py -- --blend assets/characters/goblin-warrior/highpoly/base.blend --type npc_character
python scripts/preview/render.py   -- --blend assets/characters/goblin-warrior/highpoly/base.blend --out /tmp/best.png
```

## 解剖学知識のモデルへの反映

人間・動物の関節の仕組みは2つの経路で3Dモデルに反映される:

1. **知識ベース → 検査 → 学習**: `config/anatomy.yaml` に関節タイプと可動域
   （人間: 膝0–150°・肘0–145°など / 四足動物: stifle・hock など）を定義。
   検査がポーズの解剖学的妥当性を判定し、学習ループが可動域を試行錯誤で獲得する。
2. **知識ベース → リグ**: 生成されるアーマチュア(`RIG_*`)の各ボーンに、
   可動域が **Limit Rotation 制約**として焼き込まれる。
   以後このリグでポーズ付けすると物理的に不可能な関節曲げができない。

生成器(`scripts/lib/humanoid.py`)は股関節・膝・肩・肘・体幹の角度パラメータを持ち、
関節位置を運動学（大腿方向→膝位置→足首位置）で計算してポーズ付きの体を組む。

## 実測例（goblin-warrior, 200試行・2セッション継続学習）

- **失敗率の推移**: 序盤 13/20 → 終盤 0/20（セッション1）。
  継続セッション2では最初から失敗 7/80 に抑制（知識を引き継ぐため）
- **スコア**: ベスト 76.4（120試行） → **85.8**（200試行）
- **学習した可動域**: 5関節すべてで真の解剖学値に収束
  （提案側はROMを知らされず、違反を踏んで学んだ）
- **事前回避**: 149回。学習済み制約が生成前に提案を補正し、無駄な失敗を防いだ

## 四足動物への拡張

`scripts/lib/quadruped.py` はイヌ科の骨格構造を持つ生成器。
後肢は **大腿 → stifle(膝) → 下腿 → hock(飛節) → 中足** の3節で、
stifle は伸びきらず hock は逆向きに曲がって見える、というイヌ科の特徴を運動学で再現する。
`asset.yaml` に `generator: quadruped` / `species: quadruped_canine` と書くだけで
同じ学習ループ・同じ知識ベース機構がそのまま使える。

実測（dire-wolf, 150試行）: 関節6つのROMが狭いため初期失敗率 22/30 → 学習後 2/30。
肘 19.8–150.8°（真値 20–150）、hock 29.6–140.1°（真値 30–140）などに収束した。

## AI視覚レビューを報酬に組み込む（Phase 1）

数値評価（目標一致＋ポリ効率）は「見た目の良さ」を測れない。
`scripts/learn/visual_review.py` がこれを補う:

```bash
# 1) 上位候補をレンダリングしてレビュー依頼を生成
python scripts/learn/visual_review.py -- --asset assets/characters/goblin-warrior --top 4
# 2) AI(agents/modeler.md の役割)が learn/review_scores.json に 0-10 で採点
# 3) ブレンドして知識ベースを再ランク
python scripts/learn/visual_review.py -- --asset assets/characters/goblin-warrior --apply
```

`blended = engine_score + 2.0 × visual(0-10)`。再ランクは top_k / best / sweet spot に
反映されるため、**次回の optimizer 実行は美的評価の方向へ探索する**。

実測: ゴブリンではエンジン1位(85.8)の候補が腕の不自然さで visual 6 に留まり、
エンジン2位(85.28)・visual 8 の自然な立ち姿が blended 101.28 で逆転した。

運用上の注意: ブレンド済みベストはエンジンスコア単独では超えにくいため、
**最適化セッションと視覚レビューを交互に回す**のが想定サイクル。

## 批判的専門家による反復改善（actor-critic ループ）

数値最適化と1回の視覚採点だけでは「課題に対してどこが弱いか」を反復的に詰められない。
`scripts/learn/critic_loop.py` は **辛口の批評家(critic)** を改善ループに組み込む:

```
1ラウンド =
  [actor]  optimizer が現在の目標へ向けて試行錯誤
  [render] 上位候補をレンダリング（その回の試行のみ）
  [critic] AI(agents/critic.md)が課題ルーブリックで各次元を採点＋修正指示
  [apply]  指示を「目標の修正」に変換し working_target.json を更新
→ 加重平均が challenge.yaml の pass_threshold 以上になるまで繰り返す
```

ポイント:
- **課題** `challenge.yaml` に評価ルーブリック（次元と重み）と合格閾値を定義
- critic の指示は `{param, delta}` の形で**機械適用**され、生成器の定義域にクランプされる
- **物理的知見（関節可動域・ポリ境界）はラウンドを跨いで保持**し、「良さの定義」だけを更新
- ACCEPT 時は `--finalize <候補>` で **critic が承認した候補**を最終モデルに確定
  （エンジン最良ではなく批評家の選択を採用）

### 実測（goblin-warrior「戦闘待機の立ち姿」課題, 4ラウンド）

| ラウンド | 加重平均 | 批評の要点 |
|---------|---------|-----------|
| 1 | 6.3 | 脚が長く人間的。寸胴・大頭のゴブリンらしさ不足 → 脚を詰め頭を拡大、前傾を深く |
| 2 | **5.25**（悪化） | 沈め過ぎて胴が潰れ「痩せた虫」化。必要なのは屈伸でなく**量感** → 四肢を太く胴を広げ、過修正を戻す |
| 3 | 7.8 | 大幅改善。寸胴・大頭・量感が出た。あと一歩、肩幅と構えを微調整 |
| 4 | **8.2 合格** | 寸胴・大頭・太い四肢・広い肩で安定した低い構え。出荷可能水準 |

2ラウンド目の**悪化を批評家が検知して進路を修正**した点が重要で、
単調に甘く評価するのではなく批判的に分析することで改善が前進した。

### 実測2（dire-wolf「解剖学的に正確な立ち姿」課題, 10ラウンド連続実行）

閾値9.0の高精度要求で10ラウンド回した。スコアは 5.7 → 6.9 と前進したが、
真の成果は **批評家が回を追うごとに「より深い欠陥」を発見し、道具と仕様を進化させた**こと:

| ラウンド | 発見 | 対処 |
|---------|------|------|
| R2 | 胴を伸ばすと忍び寄るネコ科に退行 | 脚長を大幅増 |
| R3 | 尾が常に上向き＝**生成器の未パラメータ化** | `tail_pitch_deg` を生成器に追加 |
| R5 | 傾いた個体が上位に＝**採点に背線水平が無い** | `back_slope_deg` メトリクス追加 |
| R6 | 脚短縮＋樽胴で身長を稼ぐ**仕様の抜け道** | `shoulder_height_m`（実測キ甲高66-81cm）追加 |
| R7 | 毎ラウンドの知識全消去が収束を阻害 | 旧ベストを新目標で再採点しアンカー保持 |
| R8 | 重み勾配が弱く他項目とのトレードで誤魔化せる | back_slope/stifle/hock の重みを強化 |
| R9 | **数値監査で目標の自己矛盾を発見**（脚比率が暗黙に意味する肩高0.891m vs 明示0.78m） | front_leg_ratio を整合値へ修正 |
| R10 | 矛盾解消が結実：水平な背・接地・正しい後肢屈曲・垂れ尾が初めて同時成立 | シリーズ最良を確定 |

教訓: 精度向上の主戦場は「目標値の微調整」ではなく、**計測の穴（報酬ハッキング）と
仕様の矛盾を批評家が暴き、評価系そのものを修理する**ことだった。

### 実測3（同課題を 9.0 合格まで継続, 全17ラウンド）

R10(6.9) で停滞した後、**生成器の表現力の天井**が真の壁だと判明し、道具を強化して突破した:

| ラウンド | スコア | 転機 |
|---------|-------|------|
| R1–R10 | 5.7→6.9 | 体型・ポーズの基礎づくり、計測の穴2つと目標矛盾を修正 |
| **R11** | 7.53 | **生成器に耳・長い吻・鼻・深い胸/絞れた腰・尾の房を追加** → ひと目でオオカミに |
| R12–R14 | 8.0→8.8 | 後肢の踏み込み・首・量感を反復調整 |
| R15 | 7.92 | 後肢が一斉に後流れに退行（収束の罠） |
| **R16** | 8.9 | **`hind_reach_ratio`（後足の後方オフセット）を採点に追加** → 後肢が胴の真下に接地 |
| **R17** | **9.0 合格** | 全欠点解消。獣医解剖学の実測に接地した出荷可能なオオカミ（4,004 tris）|

累計1,302試行。9.0 到達の決め手は2つとも**「目標いじり」ではなく評価系・生成器の強化**:
表現力の天井（耳・吻）を上げたことと、繰り返す欠陥（後肢の後流れ）を**測れるように
した**こと。批評家を厳しく保つ（8.5–8.9で何ラウンドも合格させない）ことが、
安易な収束ではなく本質的な改善を引き出した。

## 使い方（critic ループ）

```bash
# 各ラウンド: お膳立て → AIが critique.json を作成 → 適用
python scripts/learn/critic_loop.py --asset assets/characters/goblin-warrior --setup
#   （agents/critic.md の役割で learn/critique.json を作成）
python scripts/learn/critic_loop.py --asset assets/characters/goblin-warrior --apply
python scripts/learn/critic_loop.py --asset assets/characters/goblin-warrior --status   # 推移確認
# 合格したら critic 承認候補を確定
python scripts/learn/critic_loop.py --asset assets/characters/goblin-warrior --finalize 2
```

## web 参照から模範を取り込む（reference grounding）

ポーズや形の目標を、手書きの当て推量ではなく **web 上の実在の参照**（解剖学文献・
ポーズ画像・動画）に基づいて決める仕組み。AI のマルチモーダル能力を「参照 → 数値
パラメータ」の橋渡しに使う。

役割分担:
- **AI（`agents/reference-scout.md`）**: web 検索・画像理解を行い、
  `references/sources.json`（出典）と `references/reference_hints.json`
  （参照から推定したパラメータ＋出典＋信頼度）を書く
- **スクリプト（`scripts/learn/reference.py`）**: ヒントを生成器の定義域で検証・
  クランプし、`learn/reference_target.json` として最適化の初期目標に反映

目標の合成順序: `asset.yaml` < **reference_target（web参照）** < `working_target（critic）`。
参照が出発点を決め、critic が仕上げる。

### 著作権と誠実さ
- 参照画像/動画**そのものはリポジトリに保存しない**。残すのは URL・出典・ライセンス
  注記と、そこから導いた**数値（測定値＝事実）**のみ
- 各値に `confidence` を付ける: `high`=文献の実測 / `medium`=複数画像から推定 /
  `low`=単一画像の目分量。自動ポーズ推定器ではないことを明示する
- 解剖学の関節角（内角, 180°=伸展）と生成器の屈曲角（0°=伸展）の換算式を `note` に記録

### 実測（dire-wolf を立位の解剖学データで接地）

web 検索で得た実測値を生成器パラメータへ換算して目標化した:

| パラメータ | 値 | 根拠（出典） |
|-----------|----|-----|
| stifle_deg | 35° | 立位の脛骨大腿角 実測平均145° → 180-145（Vet Sci 2022, high）|
| hock_deg | 45° | 立位の飛節角 約135° → 180-135（Vet Sci 2022, medium）|
| hip_pitch_deg | 26° | 頚体角144.7°・大腿前捻+27〜31°から推定（IMAIOS, medium）|
| shoulder/elbow | -15° / 22° | 前肢は「地面までまっすぐな支柱」→ ほぼ伸展（medium）|

これを初期目標に最適化し、当て推量よりも自然な四足立位に接地した。

## 使い方（web 参照）

```bash
# 1) AI が web を調べて references/sources.json と reference_hints.json を作成
#    （agents/reference-scout.md の役割）
# 2) 検証して目標に反映
python scripts/learn/reference.py --asset assets/characters/dire-wolf --apply
python scripts/learn/reference.py --asset assets/characters/dire-wolf --status
# 3) 参照接地した目標で最適化
python scripts/learn/optimizer.py -- --asset assets/characters/dire-wolf --iters 40
```

## 限界と発展

- これは**ブロッキング（プロポーション/ポーズ）**の自動探索。質感・ディテール・
  トポロジーの良し悪しは別途人＋AI(`agents/`)が担う。
- 視覚レビューは現状 Claude Code セッション内の AI が担当（ファイル経由の
  半自動）。Claude API キーがあれば全自動化も可能。
- 生成器を増やす（顔・手のディテール、鳥型・爬虫類型の骨格）ことで拡張できる。
- web 参照は現状 AI が画像を見て数値化する半自動。専用のマルカーレス・ポーズ推定
  （動画フレーム→関節角）を組み込めば、より高精度・全自動の取り込みが可能になる。
