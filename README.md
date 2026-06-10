# Character & Prop Studio

キャラクター／ゲーム小物を **一点物で作り込む** ための、Blender + AI エージェント支援の制作リポジトリです。

「ボタン一発で完成品」ではなく、**人とAIが工程ごとに協働して質を高める**ことを目的としています。
AIは創造的判断を肩代わりするのではなく、定型作業（ブロッキング生成・検査・書き出し）と
レビューを担い、作り込みは人が主導します。

## コンセプト

- **1アセット = 1プロジェクト**: 各キャラ／小物を独立したフォルダで管理し、工程ごとに成果物を残す
- **工程の明確化**: コンセプト → ブロッキング → ハイポリ → リトポ/UV → テクスチャ → 書き出し
- **自動化と人の分担**: 定型作業は `scripts/`（bpy）、創造的判断は人＋AI
- **規格の自動検査**: ポリゴン予算・スケール・命名規則を CI でチェック

## ディレクトリ構成

```
.
├── README.md
├── config/
│   └── standards.yaml        # ポリゴン予算・スケール・命名規則（規格の単一情報源）
├── docs/
│   ├── pipeline.md           # 制作パイプラインの全体像
│   ├── agents.md             # AIエージェントの役割分担と「組織化」の判断基準
│   └── conventions.md        # 命名規則・スケール・ファイル運用
├── assets/
│   └── characters/
│       └── _template/        # 新規アセットの雛形（コピーして使う）
├── scripts/                  # Blender(bpy) 自動化スクリプト
│   ├── lib/                  # 共通モジュール（生成器・採点・検査コア・規格）
│   ├── generate/             # ブロッキング等の生成
│   ├── checks/               # 検査（マニフォールド・ポリゴン数・スケール）
│   ├── learn/                # 試行錯誤で学習する最適化ループ（docs/learning.md）
│   ├── preview/              # プレビュー画像レンダリング
│   └── export/               # glb/fbx 書き出し
├── agents/                   # AIエージェントの役割定義（プロンプト）
└── .github/workflows/        # アセット規格チェックの CI
```

## はじめかた

1. 新しいアセットを始める

   ```bash
   cp -r assets/characters/_template assets/characters/my-goblin
   ```

2. `concept/` に参照画像・コンセプトを置く（→ `agents/concept-artist.md` を参照）
3. Blender でブロッキングを生成

   ```bash
   blender --background --python scripts/generate/blocking.py -- --out assets/characters/my-goblin/blocking/blocking.blend
   ```

4. 作り込み（ハイポリ → リトポ/UV → テクスチャ）
5. 検査して書き出し

   ```bash
   blender --background --python scripts/checks/validate_mesh.py -- --blend assets/characters/my-goblin/lowpoly/lowpoly.blend
   blender --background --python scripts/export/export_glb.py -- --blend assets/characters/my-goblin/lowpoly/lowpoly.blend --out assets/characters/my-goblin/export/my-goblin.glb
   ```

## 必要環境

- [Blender](https://www.blender.org/) 4.x 以降（`blender` コマンドが PATH にあること）
- Python 3.10+（CI 用の検査スクリプト）

## 試行錯誤で学習するモデリング

ブロッキングのプロポーションを、成功・失敗の記録から学習して自動で改善する
最適化ループを備えています。失敗（ポリゴン予算超過・スケール検査落ち）からは
回避制約を、成功からは良パラメータ域を学び、知識ベースに蓄積します。

```bash
python scripts/learn/optimizer.py -- --asset assets/characters/goblin-warrior --iters 60
```

仕組みの詳細は [`docs/learning.md`](docs/learning.md) を参照してください。

## ドキュメント

- [`docs/pipeline.md`](docs/pipeline.md) — 制作パイプライン全体像
- [`docs/learning.md`](docs/learning.md) — 試行錯誤で学習する最適化ループ
- [`docs/agents.md`](docs/agents.md) — AIエージェントの役割と組織化の判断
- [`docs/conventions.md`](docs/conventions.md) — 命名・スケール・運用規則
