# 制作パイプライン

一点物のキャラクター／ゲーム小物を作り込むための工程と、各工程での
「人 / AI / スクリプト」の分担をまとめます。

## 全体像

```
[1] コンセプト  →  [2] ブロッキング  →  [3] ハイポリ  →  [4] リトポ/UV  →  [5] テクスチャ  →  [6] 書き出し
     AI主導           script+人          人主導          人+script        人+AI          script
```

| 工程 | 成果物の置き場所 | 主担当 | AI / スクリプトの役割 |
|------|------------------|--------|------------------------|
| 1. コンセプト | `concept/` | 人 | AI: 参照案・ラフ・バリエーション提案（`agents/concept-artist.md`） |
| 2. ブロッキング | `blocking/` | 人 | script: プリミティブ配置の雛形生成（`scripts/generate/blocking.py`） |
| 3. ハイポリ | `highpoly/` | 人 | AI: フォルム/シルエットのレビュー（`agents/modeler.md`） |
| 4. リトポ/UV | `lowpoly/` | 人 | AI: ポリゴン配分・UV方針の助言（`agents/retopo-uv.md`）/ script: 検査 |
| 5. テクスチャ | `textures/` | 人 | AI: マテリアル設計・PBR値の助言（`agents/texture-artist.md`） |
| 6. 書き出し | `export/` | script | script: 規格検査 → glb 書き出し（`scripts/export/`） |

## 各工程の詳細

### 1. コンセプト
- 参照画像・ムードボード・寸法メモを `concept/` に集約する。
- ここでアセットの **種別**（hero/npc/prop）を決める。種別がポリゴン予算を決定する（`config/standards.yaml`）。

### 2. ブロッキング
- プロポーションを最優先で確定させる工程。ディテールは入れない。
- `scripts/generate/blocking.py` で基準スケールのプリミティブ雛形を生成し、そこから調整する。
- 出力名は命名規則（`CHR_*_LOD0` 等）に従う。

### 3. ハイポリ
- スカルプトや高密度モデリングでディテールを作り込む。
- AI には「シルエットが読めるか」「左右非対称が意図的か」などの観点でレビューさせる。

### 4. リトポ/UV
- ゲーム用の軽量メッシュ（lowpoly）を作る。ポリゴン予算は種別ごとに `standards.yaml` で定義。
- `scripts/checks/validate_mesh.py` でマニフォールド・Ngon・ポリゴン数・UV を検査する。

### 5. テクスチャ
- ベイク（ハイポリ→ロウポリ）とPBRテクスチャを作成し `textures/` に保存。
- 命名は `MAT_*` 規則に従う。

### 6. 書き出し
- 検査をパスしたら `scripts/export/export_glb.py` で glb を出力。
- トランスフォーム・モディファイア適用は `standards.yaml` の `export` 設定に従う。

## 品質ゲート

書き出し前に必ず通すべきチェック（CI でも自動実行）:

1. 命名規則（オブジェクト名・マテリアル名）
2. スケール（キャラ身長レンジ）
3. メッシュ健全性（マニフォールド / Ngon禁止 / 浮きジオメトリ禁止）
4. ポリゴン予算
5. UV の有無

これらは `config/standards.yaml` を単一情報源として `scripts/checks/` が判定します。
