# Sift — 写真選別アプリ(Phase 1 MVP)

[SPEC.md](../SPEC.md) の Phase 1 実装。Immich 上の写真から**スクリーンショット候補**と
**完全重複**を見つけ、スワイプで振り分けて、確認画面から Immich のゴミ箱へ安全に移動する。

## 実装済み(Phase 1)

| ID | 機能 |
|---|---|
| F-1 | スクリーンショット検出(ファイル名・EXIFなし・PNG・画面解像度の複合スコア) |
| F-2 | 完全重複の取り込み(Immich の重複検出API → グループ表示・★ベスト提案) |
| F-3 | スワイプ選別UI(←削除予定 / →残す / ↑お気に入り / ↓あとで、即Undo、50枚セッション) |
| F-4 | 遅延削除(削除予定 → 確認画面 → Immichゴミ箱30日。完全削除はしない) |

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

スクショ判定に使う端末の画面解像度(既定は主要 iPhone/Android を同梱):

```bash
curl -X PUT localhost:8787/api/settings \
  -H 'Content-Type: application/json' \
  -d '{"device_resolutions":["1179x2556","1290x2796"]}'
# 反映するには再スキャン
curl -X POST localhost:8787/api/jobs/scan
```

## データとリセット

- Sift は写真を複製しない。持つのは判断状態のみ(`server/sift.db`)
- やり直したいとき: サーバーを止めて `rm server/sift.db*` → 再起動(自動再スキャン)

## トラブルシューティング

- **Immich API が合わない**: Immich はバージョンでエンドポイントが変わることがある。
  `http://<immich>:2283/api/docs`(OpenAPI)と突き合わせて `server/src/immich/client.ts`
  **だけ**を直せばよい(クライアント層を分離してある)。
- **候補が出ない**: ホームの「候補を再スキャン」を実行。スクショ判定の解像度設定も確認。
