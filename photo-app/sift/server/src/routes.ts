import { Hono } from 'hono';
import { getSetting, setSetting, type Db } from './db';
import type { ImmichClient } from './immich/types';
import { runFullScanOnce } from './services/analyze';
import { applyDecisions, keepBest, undoLast, DECISIONS, type DecisionInput } from './services/decisions';
import { getGroups, getQueueItems, getQueues, getStats, getTrashPending } from './services/queues';
import { DEFAULT_RESOLUTIONS } from './services/scan';
import { commitTrash } from './services/trash';

export function createApp(db: Db, immich: ImmichClient): Hono {
  const app = new Hono();

  app.get('/api/health', async (c) => {
    const ok = await immich.ping();
    return c.json({ ok: true, immich: ok, mock: immich.mock });
  });

  app.get('/api/queues', (c) => c.json(getQueues(db)));

  app.get('/api/queues/:category', (c) => {
    const category = c.req.param('category');
    const limit = Math.min(1000, Number(c.req.query('limit') ?? 50));
    const items =
      category === 'trash_pending' ? getTrashPending(db, limit) : getQueueItems(db, category, limit);
    return c.json({ items });
  });

  app.post('/api/decisions', async (c) => {
    const body = await c.req.json().catch(() => null);
    const assetIds: unknown = body?.assetIds;
    const decision: unknown = body?.decision;
    if (!Array.isArray(assetIds) || assetIds.length === 0 || !DECISIONS.includes(decision as DecisionInput)) {
      return c.json({ error: 'assetIds(配列) と decision(keep|trash_pending|later|favorite|reset) が必要です' }, 400);
    }
    return c.json(await applyDecisions(db, immich, assetIds as string[], decision as DecisionInput));
  });

  app.post('/api/undo', async (c) => c.json(await undoLast(db, immich)));

  app.get('/api/groups', (c) => c.json({ groups: getGroups(db, c.req.query('kind') || undefined) }));

  app.post('/api/groups/:id/keep-best', async (c) => {
    const body = await c.req.json().catch(() => ({}));
    const result = keepBest(db, Number(c.req.param('id')), body?.bestAssetId);
    if (!result) return c.json({ error: 'グループが見つかりません' }, 404);
    return c.json(result);
  });

  app.post('/api/trash/commit', async (c) => c.json(await commitTrash(db, immich)));

  app.post('/api/jobs/scan', async (c) => {
    try {
      return c.json(await runFullScanOnce(db, immich));
    } catch (e) {
      return c.json({ error: `スキャン失敗: ${(e as Error).message}` }, 502);
    }
  });

  app.get('/api/stats', (c) => c.json(getStats(db)));

  const NUMERIC_SETTINGS = [
    'screenshot_threshold', //    スクショ判定スコアのしきい値(既定 0.5)
    'screenshot_min_age_days', // スクショを候補に入れるまでの日数(既定 0 = 即候補)
    'memo_threshold', //          メモ写真スコアのしきい値(既定 0.5)
    'memo_age_days', //           メモの「賞味期限切れ」日数(既定 30)
    'blur_threshold', //          ラプラシアン分散のぼやけしきい値(既定 60)
    'similar_hamming', //         類似判定のハミング距離(既定 10)
    'burst_gap_seconds', //       連写判定の撮影間隔秒数(既定 5)
    'auto_scan_hour', //          夜間自動スキャンの実行時刻 0-23(既定 3、-1 で無効)
  ];

  app.get('/api/settings', (c) => {
    const defaults: Record<string, string> = {
      screenshot_threshold: '0.5',
      screenshot_min_age_days: '0',
      memo_threshold: '0.5',
      memo_age_days: '30',
      blur_threshold: '60',
      similar_hamming: '10',
      burst_gap_seconds: '5',
      auto_scan_hour: '3',
    };
    const out: Record<string, unknown> = {
      device_resolutions: JSON.parse(getSetting(db, 'device_resolutions', JSON.stringify(DEFAULT_RESOLUTIONS))),
    };
    for (const k of NUMERIC_SETTINGS) out[k] = Number(getSetting(db, k, defaults[k]));
    return c.json(out);
  });

  app.put('/api/settings', async (c) => {
    const body = await c.req.json().catch(() => null);
    if (!body) return c.json({ error: 'JSON ボディが必要です' }, 400);
    if (Array.isArray(body.device_resolutions)) {
      setSetting(db, 'device_resolutions', JSON.stringify(body.device_resolutions));
    }
    for (const k of NUMERIC_SETTINGS) {
      if (typeof body[k] === 'number') setSetting(db, k, String(body[k]));
    }
    return c.json({ ok: true });
  });

  // サムネイルは Immich へのプロキシ(Sift は画像を保持しない。SPEC §4)
  app.get('/api/assets/:id/thumbnail', async (c) => {
    const size = c.req.query('size') === 'preview' ? 'preview' : 'thumbnail';
    try {
      const t = await immich.getThumbnail(c.req.param('id'), size);
      c.header('Content-Type', t.contentType);
      c.header('Cache-Control', 'private, max-age=86400');
      return c.body(t.body);
    } catch {
      return c.notFound();
    }
  });

  return app;
}
