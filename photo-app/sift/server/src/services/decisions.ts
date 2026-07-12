import { pushUndo, type Db } from '../db';
import type { ImmichClient } from '../immich/types';

// decision の値: keep | trash_pending | later | favorite | trashed(commit後) | NULL(未判断)
// API からは 'reset' も受け付け、NULL(未判断)へ戻す。
export const DECISIONS = ['keep', 'trash_pending', 'later', 'favorite', 'reset'] as const;
export type DecisionInput = (typeof DECISIONS)[number];

interface PrevState {
  assetId: string;
  prevDecision: string | null;
  prevDecidedAt: string | null;
}

// 複数アセットに(場合により異なる)判断を適用し、undo_log に1エントリだけ積む
function applyMixed(db: Db, entries: { assetId: string; decision: string | null }[], label: string): PrevState[] {
  const get = db.prepare(`SELECT decision, decided_at FROM asset_state WHERE asset_id = ?`);
  const upd = db.prepare(`UPDATE asset_state SET decision = ?, decided_at = datetime('now') WHERE asset_id = ?`);
  const prev: PrevState[] = [];
  const tx = db.transaction(() => {
    for (const e of entries) {
      const row = get.get(e.assetId) as { decision: string | null; decided_at: string | null } | undefined;
      if (!row) continue;
      prev.push({ assetId: e.assetId, prevDecision: row.decision, prevDecidedAt: row.decided_at });
      upd.run(e.decision, e.assetId);
    }
    if (prev.length) pushUndo(db, { type: 'decisions', label, items: prev });
  });
  tx();
  return prev;
}

// SPEC §9: RAW+JPEG ペアは必ずペア単位で扱う。判断対象にペアの片割れを自動で含める
function expandWithPairs(db: Db, assetIds: string[]): string[] {
  const stmt = db.prepare(`SELECT pair_asset_id FROM asset_state WHERE asset_id = ?`);
  const out = new Set(assetIds);
  for (const id of assetIds) {
    const r = stmt.get(id) as { pair_asset_id: string | null } | undefined;
    if (r?.pair_asset_id) out.add(r.pair_asset_id);
  }
  return [...out];
}

export async function applyDecisions(
  db: Db,
  immich: ImmichClient,
  assetIds: string[],
  decision: DecisionInput
): Promise<{ updated: number }> {
  const value = decision === 'reset' ? null : decision;
  // お気に入りは「その1枚」への操作。それ以外(削除予定・残す等)はペアに連動させる
  const targets = decision === 'favorite' ? assetIds : expandWithPairs(db, assetIds);
  const prev = applyMixed(
    db,
    targets.map((assetId) => ({ assetId, decision: value })),
    decision
  );
  // お気に入りは Immich にも反映する(SPEC S-2)
  if (decision === 'favorite') {
    const upd = db.prepare(`UPDATE asset_state SET is_favorite = 1 WHERE asset_id = ?`);
    for (const p of prev) {
      await immich.setFavorite(p.assetId, true);
      upd.run(p.assetId);
    }
  }
  return { updated: prev.length };
}

export function keepBest(db: Db, groupId: number, bestAssetId?: string): { kept: string; trashed: number } | null {
  const g = db.prepare(`SELECT id, best_asset_id FROM groups WHERE id = ?`).get(groupId) as
    | { id: number; best_asset_id: string | null }
    | undefined;
  if (!g) return null;
  const best = bestAssetId ?? g.best_asset_id;
  if (!best) return null;
  const members = db
    .prepare(
      `SELECT asset_id, is_favorite, pair_asset_id FROM asset_state
       WHERE group_id = ? AND (decision IS NULL OR decision = 'later')`
    )
    .all(groupId) as { asset_id: string; is_favorite: number; pair_asset_id: string | null }[];

  const entries: { assetId: string; decision: string }[] = [];
  const add = (assetId: string, decision: string) => {
    if (!entries.some((e) => e.assetId === assetId)) entries.push({ assetId, decision });
  };
  // best(とそのRAWペア)を先に keep 登録してから、残りを削除予定にする
  const bestMember = members.find((m) => m.asset_id === best);
  add(best, 'keep');
  if (bestMember?.pair_asset_id) add(bestMember.pair_asset_id, 'keep');
  let trashed = 0;
  for (const m of members) {
    if (m.asset_id === best) continue;
    if (m.is_favorite) continue; // SPEC §9: お気に入りは一括操作で削除予定にしない
    add(m.asset_id, 'trash_pending');
    if (m.pair_asset_id) add(m.pair_asset_id, 'trash_pending');
  }
  trashed = entries.filter((e) => e.decision === 'trash_pending').length;
  if (trashed === 0) return { kept: best, trashed: 0 };
  applyMixed(db, entries, 'keep-best');
  return { kept: best, trashed };
}

export async function undoLast(db: Db, immich: ImmichClient): Promise<{ undone: string | null }> {
  const row = db.prepare(`SELECT id, action_json FROM undo_log ORDER BY id DESC LIMIT 1`).get() as
    | { id: number; action_json: string }
    | undefined;
  if (!row) return { undone: null };
  const action = JSON.parse(row.action_json) as {
    type: string;
    label?: string;
    items?: PrevState[];
    ids?: string[];
  };

  if (action.type === 'decisions' && action.items) {
    const upd = db.prepare(`UPDATE asset_state SET decision = ?, decided_at = ? WHERE asset_id = ?`);
    const tx = db.transaction(() => {
      for (const it of action.items!) upd.run(it.prevDecision, it.prevDecidedAt, it.assetId);
      db.prepare(`DELETE FROM undo_log WHERE id = ?`).run(row.id);
    });
    tx();
    if (action.label === 'favorite') {
      const updFav = db.prepare(`UPDATE asset_state SET is_favorite = 0 WHERE asset_id = ?`);
      for (const it of action.items) {
        await immich.setFavorite(it.assetId, false);
        updFav.run(it.assetId);
      }
    }
    return { undone: 'decisions' };
  }

  if (action.type === 'trash_commit' && action.ids) {
    // まず Immich 側を復元(失敗したら undo_log は残る=再試行できる)
    await immich.restoreAssets(action.ids);
    const tx = db.transaction(() => {
      const upd = db.prepare(`UPDATE asset_state SET decision = 'trash_pending' WHERE asset_id = ?`);
      for (const id of action.ids!) upd.run(id);
      db.prepare(`DELETE FROM undo_log WHERE id = ?`).run(row.id);
    });
    tx();
    return { undone: 'trash_commit' };
  }

  db.prepare(`DELETE FROM undo_log WHERE id = ?`).run(row.id);
  return { undone: null };
}
