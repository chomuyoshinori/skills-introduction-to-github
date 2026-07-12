import type { Db } from '../db';

export interface QueueItem {
  id: string;
  fileName: string | null;
  takenAt: string | null;
  sizeBytes: number;
  width: number | null;
  height: number | null;
  score: number;
  decision: string | null;
  sharpness: number | null;
}

const ITEM_COLS = `asset_id, file_name, taken_at, size_bytes, width, height, score, decision, sharpness`;

function toItem(r: Record<string, unknown>): QueueItem {
  return {
    id: r.asset_id as string,
    fileName: r.file_name as string | null,
    takenAt: r.taken_at as string | null,
    sizeBytes: (r.size_bytes as number) ?? 0,
    width: r.width as number | null,
    height: r.height as number | null,
    score: (r.score as number) ?? 0,
    decision: r.decision as string | null,
    sharpness: r.sharpness as number | null,
  };
}

// カテゴリ別キュー: 未判断(+「あとで」は末尾)のみ。お気に入りは除外(SPEC §6.4)
export function getQueueItems(db: Db, category: string, limit = 50): QueueItem[] {
  const rows = db
    .prepare(
      `SELECT ${ITEM_COLS} FROM asset_state
       WHERE category = ? AND (decision IS NULL OR decision = 'later') AND is_favorite = 0
       ORDER BY (decision IS NOT NULL) ASC, score DESC, taken_at DESC
       LIMIT ?`
    )
    .all(category, limit) as Record<string, unknown>[];
  return rows.map(toItem);
}

export function getTrashPending(db: Db, limit = 1000): QueueItem[] {
  const rows = db
    .prepare(
      `SELECT ${ITEM_COLS} FROM asset_state
       WHERE decision = 'trash_pending'
       ORDER BY taken_at DESC
       LIMIT ?`
    )
    .all(limit) as Record<string, unknown>[];
  return rows.map(toItem);
}

export interface QueuesSummary {
  screenshot: { count: number; bytes: number };
  memo: { count: number; bytes: number };
  blurry: { count: number; bytes: number };
  groups: { count: number; bytes: number };
  trashPending: { count: number; bytes: number };
}

function categorySummary(db: Db, category: string): { count: number; bytes: number } {
  const r = db
    .prepare(
      `SELECT COUNT(*) c, COALESCE(SUM(size_bytes), 0) b FROM asset_state
       WHERE category = ? AND (decision IS NULL OR decision = 'later') AND is_favorite = 0`
    )
    .get(category) as { c: number; b: number };
  return { count: r.c, bytes: r.b };
}

// アクション可能なグループ = 未判断メンバーが2枚以上。解放見込み = ベスト以外の未判断分
function groupsSummary(db: Db): { count: number; bytes: number } {
  const rows = db
    .prepare(
      `SELECT g.id,
              SUM(CASE WHEN a.decision IS NULL OR a.decision = 'later' THEN 1 ELSE 0 END) undecided,
              SUM(CASE WHEN (a.decision IS NULL OR a.decision = 'later') AND a.asset_id != g.best_asset_id THEN a.size_bytes ELSE 0 END) potential
       FROM groups g JOIN asset_state a ON a.group_id = g.id
       GROUP BY g.id
       HAVING undecided >= 2`
    )
    .all() as { id: number; undecided: number; potential: number }[];
  return { count: rows.length, bytes: rows.reduce((s, r) => s + (r.potential || 0), 0) };
}

export function getQueues(db: Db): QueuesSummary {
  const trash = db
    .prepare(`SELECT COUNT(*) c, COALESCE(SUM(size_bytes), 0) b FROM asset_state WHERE decision = 'trash_pending'`)
    .get() as { c: number; b: number };
  return {
    screenshot: categorySummary(db, 'screenshot'),
    memo: categorySummary(db, 'memo'),
    blurry: categorySummary(db, 'blurry'),
    groups: groupsSummary(db),
    trashPending: { count: trash.c, bytes: trash.b },
  };
}

export interface GroupView {
  id: number;
  kind: string;
  bestAssetId: string | null;
  assets: (QueueItem & { isFavorite: boolean })[];
}

export function getGroups(db: Db, kind?: string): GroupView[] {
  const groups = (
    kind
      ? db.prepare(`SELECT id, kind, best_asset_id FROM groups WHERE kind = ?`).all(kind)
      : db.prepare(`SELECT id, kind, best_asset_id FROM groups`).all()
  ) as { id: number; kind: string; best_asset_id: string | null }[];
  const membersStmt = db.prepare(
    `SELECT ${ITEM_COLS}, is_favorite FROM asset_state WHERE group_id = ? ORDER BY size_bytes DESC`
  );
  const out: GroupView[] = [];
  for (const g of groups) {
    const members = (membersStmt.all(g.id) as Record<string, unknown>[]).map((r) => ({
      ...toItem(r),
      isFavorite: Boolean(r.is_favorite),
    }));
    const undecided = members.filter((m) => m.decision === null || m.decision === 'later').length;
    if (undecided < 2) continue; // 判断済みグループは出さない
    out.push({ id: g.id, kind: g.kind, bestAssetId: g.best_asset_id, assets: members });
  }
  // 新しい写真のグループから順に
  out.sort((a, b) => (b.assets[0]?.takenAt ?? '').localeCompare(a.assets[0]?.takenAt ?? ''));
  return out;
}

export interface Stats {
  freedBytes: number;
  trashedCount: number;
  reviewedCount: number;
  remaining: { screenshot: number; memo: number; blurry: number; groups: number };
  monthlyFreed: { month: string; bytes: number; count: number }[];
}

export function getStats(db: Db): Stats {
  const freed = db
    .prepare(`SELECT COUNT(*) c, COALESCE(SUM(size_bytes), 0) b FROM asset_state WHERE decision = 'trashed'`)
    .get() as { c: number; b: number };
  const reviewed = db
    .prepare(`SELECT COUNT(*) c FROM asset_state WHERE decision IS NOT NULL AND decision != 'later'`)
    .get() as { c: number };
  const q = getQueues(db);
  const monthly = db
    .prepare(
      `SELECT substr(decided_at, 1, 7) month, COALESCE(SUM(size_bytes), 0) bytes, COUNT(*) count
       FROM asset_state WHERE decision = 'trashed' AND decided_at IS NOT NULL
       GROUP BY month ORDER BY month DESC LIMIT 12`
    )
    .all() as { month: string; bytes: number; count: number }[];
  return {
    freedBytes: freed.b,
    trashedCount: freed.c,
    reviewedCount: reviewed.c,
    remaining: {
      screenshot: q.screenshot.count,
      memo: q.memo.count,
      blurry: q.blurry.count,
      groups: q.groups.count,
    },
    monthlyFreed: monthly,
  };
}
