# Sift — 写真選別アプリ(Phase 1 + 2)

[SPEC.md](../SPEC.md) の Phase 1・2 実装。Immich 上の写真から**スクショ・メモ写真・ぼやけ・
重複・連写・類似**を見つけ、スワイプとグループ比較で振り分けて、確認画面から Immich の
ゴミ箱へ安全に移動する。

## 実装済み

| ID | 機能 | Phase |
|---|---|:-:|
| F-1 | スクリーンショット検出(ファイル名・EXIFなし・PNG・画面解像度の複合スコア) | 1 |
| F-2 | 完全重複の取り込み(Immich の重複検出API → グループ表示・★ベスト提案) | 1 |
| F-3 | スワイプ選別UI(←削除予定 / →残す / ↑お気に入り / ↓あとで、即Undo、50枚セッション) | 1 |
| F-4 | 遅延削除(削除予定 → 確認画面 → Immichゴミ箱30日。完全削除はしない) | 1 |
| F-5 | 類似・連写グループ化(同一カメラ±5秒=連写 / 同日内 pHash 距離=類似) | 2 |
| F-6 | ベストショット提案(シャープネス=ラプラシアン分散)+ 2枚拡大比較ビュー | 2 |
| F-7 | メモ写真検出(Immich CLIP検索 + 書類ヒューリスティック + 経過日数) | 2 |
| F-8 | ぼやけ写真検出(低シャープネス) | 2 |
| F-9 | 統計画面(解放容量・レビュー数・残り候補・月別実績) | 2 |

### Phase 2 の実装メモ

- 画像解析は**サムネイル1枚の取得だけ**で行う(pHash / シャープネス / 書類度)。原本には触れない。
  解析は増分式で、2回目以降のスキャンは新規アセットのみ解析する。
- SPEC §6.2 の OCR は、Phase 2 では軽量な**書類ヒューリスティック**(低彩度+白背景+高エッジ密度)
  と Immich の CLIP 検索の組み合わせで代替した。本格 OCR(Tesseract / macOS Vision)は Phase 3 候補。
- しきい値は設定 API で調整可能(下記)。既定値はモックライブラリで
  「ぼやけ 37〜41 vs 鮮明 395以上」と明確に分離することを確認して決めた。

## セットアップ(Mac mini 上)

```bash
cd photo-app/sift
npm install
cp .env.example .env    # IMMICH_URL と IMMICH_API_KEY を記入
npm run build           # フロントエンドをビルド
npm run start           # → http://localhost:8787
```

- Immich の API キー: Immich Web → 右上アイコン → **Account Settings → API Keys → New API Key**
- 初回起動時に自動でライブラリをスキャンする(以後はホームの「候補を再スキャン」)
- スマホからは Tailscale 経由で `http://<Mac miniのTailscale名>:8787` を開く

## Immich なしで試す(モックモード)

```bash
SIFT_MOCK=1 npm run start
```

ダミー写真(スクショ24枚・重複5組・通常40枚)で全フローを体験できる。DBを分けたい場合は
`SIFT_DB=./mock.db` も併せて指定。

## 開発

```bash
npm run dev:server   # ターミナル1: APIサーバー (8787)
npm run dev:web      # ターミナル2: Vite dev server (5173, /api は 8787 へプロキシ)
npm run typecheck    # 型チェック
```

## 設定

`GET /api/settings` で現在値を確認、`PUT /api/settings` で変更できる(反映には再スキャン)。

| キー | 既定 | 意味 |
|---|---|---|
| `device_resolutions` | 主要 iPhone/Android | スクショ判定に使う端末画面解像度 |
| `screenshot_threshold` | 0.5 | スクショ判定スコアのしきい値 |
| `memo_threshold` | 0.5 | メモ写真スコアのしきい値 |
| `memo_age_days` | 30 | メモの「賞味期限切れ」日数 |
| `blur_threshold` | 60 | ぼやけ判定(ラプラシアン分散がこれ未満) |
| `similar_hamming` | 10 | 類似判定の pHash ハミング距離(0〜64) |
| `burst_gap_seconds` | 5 | 連写判定の撮影間隔 |

```bash
curl -X PUT localhost:8787/api/settings \
  -H 'Content-Type: application/json' \
  -d '{"device_resolutions":["1179x2556","1290x2796"],"blur_threshold":60}'
curl -X POST localhost:8787/api/jobs/scan   # 反映
```

## データとリセット

- Sift は写真を複製しない。持つのは判断状態のみ(`server/sift.db`)
- やり直したいとき: サーバーを止めて `rm server/sift.db*` → 再起動(自動再スキャン)

## トラブルシューティング

- **Immich API が合わない**: Immich はバージョンでエンドポイントが変わることがある。
  `http://<immich>:2283/api/docs`(OpenAPI)と突き合わせて `server/src/immich/client.ts`
  **だけ**を直せばよい(クライアント層を分離してある)。
- **候補が出ない**: ホームの「候補を再スキャン」を実行。スクショ判定の解像度設定も確認。
