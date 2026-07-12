import type { DuplicateGroup, ImmichAsset, ImmichClient, Thumb } from './types';

// ─────────────────────────────────────────────────────────────
// Immich REST API を叩く薄いクライアント層(SPEC §12)。
// エンドポイントは Immich のバージョンで変わることがある。
// 動かない場合は http://<immich>/api/docs (OpenAPI) と突き合わせて
// 【このファイルだけ】を修正すればよい。
// ─────────────────────────────────────────────────────────────
export function createImmichClient(baseUrl: string, apiKey: string): ImmichClient {
  const baseHeaders: Record<string, string> = {
    'x-api-key': apiKey,
    Accept: 'application/json',
  };

  async function call(path: string, init: RequestInit = {}): Promise<Response> {
    const headers: Record<string, string> = { ...baseHeaders };
    if (init.body) headers['Content-Type'] = 'application/json';
    const res = await fetch(baseUrl + path, { ...init, headers });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Immich API ${init.method ?? 'GET'} ${path} -> ${res.status} ${text.slice(0, 300)}`);
    }
    return res;
  }

  return {
    mock: false,

    async ping() {
      try {
        const res = await fetch(baseUrl + '/api/server/ping', { headers: baseHeaders });
        return res.ok;
      } catch {
        return false;
      }
    },

    async fetchAllAssets() {
      const all: ImmichAsset[] = [];
      let page: number | null = 1;
      while (page !== null) {
        const res = await call('/api/search/metadata', {
          method: 'POST',
          body: JSON.stringify({ page, size: 1000, withExif: true, type: 'IMAGE' }),
        });
        const data = (await res.json()) as {
          assets?: { items?: ImmichAsset[]; nextPage?: string | number | null };
        };
        all.push(...(data.assets?.items ?? []));
        const next = data.assets?.nextPage;
        page = next ? Number(next) : null;
      }
      return all;
    },

    async getDuplicates() {
      const res = await call('/api/duplicates');
      return (await res.json()) as DuplicateGroup[];
    },

    async trashAssets(ids) {
      // force: false → Immich のゴミ箱へ(30日で自動完全削除)
      await call('/api/assets', { method: 'DELETE', body: JSON.stringify({ ids, force: false }) });
    },

    async restoreAssets(ids) {
      await call('/api/trash/restore/assets', { method: 'POST', body: JSON.stringify({ ids }) });
    },

    async setFavorite(id, isFavorite) {
      await call(`/api/assets/${id}`, { method: 'PUT', body: JSON.stringify({ isFavorite }) });
    },

    async getThumbnail(id, size): Promise<Thumb> {
      const res = await call(`/api/assets/${id}/thumbnail?size=${size}`);
      return {
        contentType: res.headers.get('content-type') ?? 'image/jpeg',
        body: await res.arrayBuffer(),
      };
    },

    async smartSearch(query) {
      const res = await call('/api/search/smart', {
        method: 'POST',
        body: JSON.stringify({ query, size: 250 }),
      });
      const data = (await res.json()) as { assets?: { items?: { id: string }[] } };
      return (data.assets?.items ?? []).map((a) => a.id);
    },
  };
}
