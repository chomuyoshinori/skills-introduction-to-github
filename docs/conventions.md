# 命名・スケール・ファイル運用規則

機械検査の単一情報源は [`config/standards.yaml`](../config/standards.yaml) です。
本ドキュメントはその意図を人向けに補足します。

## スケール

- **1 Blender unit = 1 メートル**。シーン単位は Metric / 1.0 に統一。
- キャラは原点（足元が Z=0）に立たせる。
- 想定身長は 0.3m〜3.0m の範囲（極端なスケールミスを検査で検出）。

## オブジェクト命名

```
<種別>_<名前>_<部位>_LOD<n>
```

- 種別: `CHR`（キャラクター） / `PRP`（プロップ）
- 名前・部位: 小文字英数字とアンダースコア（例: `goblin`, `body`, `axe`）
- LOD: `LOD0`（最高精細）〜 `LOD3`

例:
- `CHR_goblin_body_LOD0`
- `PRP_treasure_chest_LOD0`

## マテリアル命名

```
MAT_<名前>
```

例: `MAT_goblin_skin`, `MAT_chest_wood`

## 種別とポリゴン予算

| 種別 | 用途 | 予算 (lowpoly) |
|------|------|----------------|
| hero_character | 寄りで見せる主役キャラ | 60,000 tris |
| npc_character | モブ・NPC | 25,000 tris |
| prop_large | 樽・宝箱など | 15,000 tris |
| prop_small | 小アイテム | 4,000 tris |

## メッシュ健全性

- 多様体（manifold）であること
- Ngon（5角以上の面）禁止 — 三角・四角のみ
- 浮いた頂点・辺（loose geometry）禁止
- UV を持つこと

## アセットフォルダ構成（1アセット = 1フォルダ）

```
assets/characters/<name>/
├── concept/     # 参照画像・ムードボード・寸法メモ
├── blocking/    # プロポーション確定用
├── highpoly/    # 作り込み（スカルプト等）
├── lowpoly/     # ゲーム用軽量メッシュ
├── textures/    # ベイク済み / PBR テクスチャ
├── export/      # glb など最終書き出し
└── asset.yaml   # このアセットのメタ情報（種別・予算など）
```

## バージョン管理の注意

- `.blend` などのバイナリは Git LFS の利用を推奨（大規模化時）。現状の `.gitignore` で
  巨大な中間ファイルは除外しています。
- `export/` の最終成果物と `asset.yaml` は必ずコミットする。
