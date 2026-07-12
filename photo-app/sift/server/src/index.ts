import { serve } from '@hono/node-server';
import { serveStatic } from '@hono/node-server/serve-static';
import { config } from './config';
import { openDb } from './db';
import { createImmichClient } from './immich/client';
import { createMockImmich } from './immich/mock';
import { createApp } from './routes';
import { runFullScanOnce } from './services/analyze';

const immich = config.mock ? createMockImmich() : createImmichClient(config.immichUrl, config.immichApiKey);
const db = openDb();
const app = createApp(db, immich);

// ビルド済みフロントエンド(web/dist)を配信。開発時は Vite(5173)が UI を担当
app.use('*', serveStatic({ root: '../web/dist' }));

serve({ fetch: app.fetch, port: config.port }, (info) => {
  console.log(`Sift サーバー起動: http://localhost:${info.port} ${config.mock ? '(モックモード)' : ''}`);
});

if (config.mock) {
  console.log('SIFT_MOCK=1: Immich の代わりにダミー写真ライブラリを使います');
} else {
  immich.ping().then((ok) => {
    if (!ok) console.warn(`⚠ Immich (${config.immichUrl}) に接続できません。IMMICH_URL / IMMICH_API_KEY を確認してください`);
  });
}

// 初回起動時(DBが空のとき)は自動でスキャンを開始する
const count = db.prepare(`SELECT COUNT(*) c FROM asset_state`).get() as { c: number };
if (count.c === 0) {
  console.log('初回スキャン(画像解析込み)を開始します…');
  runFullScanOnce(db, immich)
    .then((r) =>
      console.log(
        `スキャン完了: ${r.scanned}枚 / スクショ${r.screenshots} メモ${r.memo} ぼやけ${r.blurry} / ` +
          `重複${r.duplicateGroups}組 連写${r.burstGroups}組 類似${r.similarGroups}組(解析${r.analyzed}枚 失敗${r.analyzeFailed})`
      )
    )
    .catch((e) => console.error('初回スキャン失敗:', (e as Error).message));
}
