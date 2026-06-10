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
| `scripts/lib/humanoid.py` | パラメトリックな人体生成器（球＋円柱、Ngon/非多様体を出さない）。探索する**パラメータ定義域**もここ |
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

## 実測例（goblin-warrior, 60試行）

- スコア: 初期 ~68 → ベスト **90.06**、プロポーション誤差 0.31 → 0.10
- 失敗1回(予算超過 seg=185)を踏んで `seg_cap` を学習 → 以降の過大 seg 提案を
  生成前に補正（事前回避）
- ベスト: height 1.27m / 頭比率 0.30 / 前傾 11° / 234 tris

## 限界と発展

- これは**ブロッキング（プロポーション）**の自動探索。質感・ディテール・
  トポロジーの良し悪しは別途人＋AI(`agents/`)が担う。
- スコア関数は「目標との一致＋ポリ効率」。シルエットの美的評価を入れたい場合は、
  レンダリング画像を AI(modeler) に採点させて報酬に組み込む拡張が考えられる
  （`docs/agents.md` の Phase 1 と接続）。
- 生成器を増やす（顔・手のディテール用パーツ、ボーン）ことで探索空間を拡張できる。
