import { Hono } from 'hono';
import { getSetting, setSetting, type Db } from './db';
import type { ImmichClient } from './immich/types';
import { applyDecisions, keepBest, undoLast, DECISIONS, type DecisionInput } from './services/decisions';
import { getGroups, getQueueItems, getQueues, getStats, getTrashPending } from './services/queues';
import { DEFAULT_RESOLUTIONS, runScanOnce } from './services/scan';
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

  app.get('/api/groups', (c) => c.json({ groups: getGroups(db, c.req.query('kind') ?? 'duplicate') }));

  app.post('/api/groups/:id/keep-best', async (c) => {
    const body = await c.req.json().catch(() => ({}));
    const result = keepBest(db, Number(c.req.param('id')), body?.bestAssetId);
    if (!result) return c.json({ error: 'グループが見つかりません' }, 404);
    return c.json(result);
  });

  app.post('/api/trash/commit', async (c) => c.json(await commitTrash(db, immich)));

  app.post('/api/jobs/scan', async (c) => {
    try {
      return c.json(await runScanOnce(db, immich));
    } catch (e) {
      return c.json({ error: `スキャン失敗: ${(e as Error).message}` }, 502);
    }
  });

  app.get('/api/stats', (c) => c.json(getStats(db)));

  app.get('/api/settings', (c) =>
    c.json({
      device_resolutions: JSON.parse(getSetting(db, 'device_resolutions', JSON.stringify(DEFAULT_RESOLUTIONS))),
      screenshot_threshold: Number(getSetting(db, 'screenshot_threshold', '0.5')),
    })
  );

  app.put('/api/settings', async (c) => {
    const body = await c.req.json().catch(() => null);
    if (!body) return c.json({ error: 'JSON ボディが必要です' }, 400);
    if (Array.isArray(body.device_resolutions)) {
      setSetting(db, 'device_resolutions', JSON.stringify(body.device_resolutions));
    }
    if (typeof body.screenshot_threshold === 'number') {
      setSetting(db, 'screenshot_threshold', String(body.screenshot_threshold));
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
