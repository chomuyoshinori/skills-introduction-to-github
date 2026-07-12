export type Decision = 'keep' | 'trash_pending' | 'later' | 'favorite' | 'reset';

export interface AssetItem {
  id: string;
  fileName: string | null;
  takenAt: string | null;
  sizeBytes: number;
  width: number | null;
  height: number | null;
  score: number;
  decision: string | null;
}

export interface QueuesRes {
  screenshot: { count: number; bytes: number };
  duplicates: { groups: number; bytes: number };
  trashPending: { count: number; bytes: number };
}

export interface Stats {
  freedBytes: number;
  trashedCount: number;
  reviewedCount: number;
}

export interface Group {
  id: number;
  kind: string;
  bestAssetId: string | null;
  assets: (AssetItem & { isFavorite: boolean })[];
}

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const withJson =
    init?.body != null
      ? { ...init, headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) } }
      : init;
  const res = await fetch(path, withJson);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => j<{ ok: boolean; immich: boolean; mock: boolean }>('/api/health'),
  queues: () => j<QueuesRes>('/api/queues'),
  queueItems: (category: string, limit = 50) =>
    j<{ items: AssetItem[] }>(`/api/queues/${category}?limit=${limit}`),
  decide: (assetIds: string[], decision: Decision) =>
    j<{ updated: number }>('/api/decisions', { method: 'POST', body: JSON.stringify({ assetIds, decision }) }),
  undo: () => j<{ undone: string | null }>('/api/undo', { method: 'POST' }),
  groups: (kind = 'duplicate') => j<{ groups: Group[] }>(`/api/groups?kind=${kind}`),
  keepBest: (id: number, bestAssetId?: string) =>
    j<{ kept: string; trashed: number }>(`/api/groups/${id}/keep-best`, {
      method: 'POST',
      body: JSON.stringify({ bestAssetId }),
    }),
  commitTrash: () => j<{ moved: number; bytes: number }>('/api/trash/commit', { method: 'POST' }),
  scan: () =>
    j<{ scanned: number; screenshots: number; duplicateGroups: number }>('/api/jobs/scan', { method: 'POST' }),
  stats: () => j<Stats>('/api/stats'),
};

export function thumbUrl(id: string, size: 'thumbnail' | 'preview' = 'thumbnail'): string {
  return `/api/assets/${id}/thumbnail?size=${size}`;
}

export function fmtBytes(n: number): string {
  if (n <= 0) return '0MB';
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}GB`;
  if (n >= 1e6) return `${Math.round(n / 1e6)}MB`;
  return `${Math.max(1, Math.round(n / 1e3))}KB`;
}

export function fmtDate(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('ja-JP', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function fmtMonth(iso: string | null): string {
  if (!iso) return '不明';
  const d = new Date(iso);
  return d.toLocaleDateString('ja-JP', { year: 'numeric', month: 'long' });
}
