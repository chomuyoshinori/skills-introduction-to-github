import { pushUndo, type Db } from '../db';
import type { ImmichClient } from '../immich/types';

// SPEC §9 遅延実行: ここが Immich への唯一の「削除系」書き込み。
// ゴミ箱移動のみで完全削除はしない(30日復元は Immich 標準機能)。
export async function commitTrash(db: Db, immich: ImmichClient): Promise<{ moved: number; bytes: number }> {
  const rows = db
    .prepare(`SELECT asset_id, size_bytes FROM asset_state WHERE decision = 'trash_pending'`)
    .all() as { asset_id: string; size_bytes: number }[];
  const ids = rows.map((r) => r.asset_id);
  if (ids.length === 0) return { moved: 0, bytes: 0 };

  await immich.trashAssets(ids);

  const bytes = rows.reduce((s, r) => s + (r.size_bytes || 0), 0);
  const tx = db.transaction(() => {
    const upd = db.prepare(`UPDATE asset_state SET decision = 'trashed', decided_at = datetime('now') WHERE asset_id = ?`);
    for (const id of ids) upd.run(id);
    pushUndo(db, { type: 'trash_commit', ids });
  });
  tx();
  return { moved: ids.length, bytes };
}
