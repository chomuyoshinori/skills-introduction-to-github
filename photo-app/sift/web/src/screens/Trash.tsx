import { useEffect, useMemo, useState } from 'react';
import { api, fmtBytes, fmtMonth, thumbUrl, type AssetItem } from '../api';
import { Toast, useToast } from '../components/Toast';

// SPEC S-4: 削除予定の確認 = 実行ゲート。ここで初めて Immich のゴミ箱へ移動する
export function Trash() {
  const [items, setItems] = useState<AssetItem[] | null>(null);
  const [committed, setCommitted] = useState<{ moved: number; bytes: number } | null>(null);
  const [busy, setBusy] = useState(false);
  const { toast, showToast, hideToast } = useToast();

  const load = () => {
    setCommitted(null);
    api.queueItems('trash_pending', 1000).then((r) => setItems(r.items));
  };
  useEffect(load, []);

  const totalBytes = useMemo(() => (items ?? []).reduce((s, a) => s + a.sizeBytes, 0), [items]);
  const byMonth = useMemo(() => {
    const m = new Map<string, AssetItem[]>();
    for (const a of items ?? []) {
      const k = fmtMonth(a.takenAt);
      m.set(k, [...(m.get(k) ?? []), a]);
    }
    return [...m.entries()];
  }, [items]);

  async function restore(a: AssetItem) {
    await api.decide([a.id], 'reset');
    setItems((xs) => xs?.filter((x) => x.id !== a.id) ?? null);
    showToast('削除予定を取り消しました');
  }

  async function commit() {
    if (!items?.length) return;
    setBusy(true);
    try {
      const r = await api.commitTrash();
      setCommitted(r);
      setItems([]);
      // SPEC S-4: 実行後60秒は一括で元に戻せる
      showToast(`${fmtBytes(r.bytes)}分をゴミ箱へ移動しました`, {
        action: '元に戻す',
        onAction: async () => {
          await api.undo();
          load();
        },
        ms: 60_000,
      });
    } catch {
      showToast('ゴミ箱への移動に失敗しました(Immich接続を確認)', { ms: 4000 });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 pb-36 pt-4">
      <header className="mb-4 flex items-center gap-3">
        <a href="#/" className="text-neutral-400">←</a>
        <h1 className="font-bold">
          削除予定 {items && items.length > 0 && `${items.length}枚 ≈${fmtBytes(totalBytes)}`}
        </h1>
      </header>

      {items === null && <p className="text-center text-neutral-500">読み込み中…</p>}

      {committed && (
        <div className="mb-4 rounded-2xl border border-emerald-900 bg-emerald-950/40 p-4 text-sm">
          <p className="font-bold text-emerald-300">
            {committed.moved}枚({fmtBytes(committed.bytes)})をゴミ箱へ移動しました
          </p>
          <p className="mt-1 text-neutral-400">Immich のゴミ箱で30日間はいつでも復元できます。</p>
          <a href="#/" className="mt-2 inline-block text-sky-400">ホームへ戻る →</a>
        </div>
      )}

      {items !== null && items.length === 0 && !committed && (
        <p className="mt-16 text-center text-neutral-400">削除予定はありません</p>
      )}

      {byMonth.map(([month, list]) => (
        <section key={month} className="mb-5">
          <h2 className="mb-2 text-sm text-neutral-400">
            {month}({list.length}枚)
          </h2>
          <div className="grid grid-cols-4 gap-1.5">
            {list.map((a) => (
              <button key={a.id} onClick={() => restore(a)} className="relative overflow-hidden rounded-lg">
                <img src={thumbUrl(a.id)} alt="" className="aspect-square w-full object-cover" draggable={false} />
                <span className="absolute inset-x-0 bottom-0 bg-black/60 py-0.5 text-center text-[9px]">
                  タップで取り消し
                </span>
              </button>
            ))}
          </div>
        </section>
      ))}

      {items !== null && items.length > 0 && (
        <div className="fixed bottom-0 left-1/2 w-[min(100%,28rem)] -translate-x-1/2 bg-gradient-to-t from-neutral-950 via-neutral-950/95 to-transparent px-4 pb-6 pt-8">
          <button
            onClick={commit}
            disabled={busy}
            className="w-full rounded-2xl bg-neutral-200 py-4 font-bold text-neutral-900 disabled:opacity-50"
          >
            🗑 {items.length}枚をゴミ箱へ移動
          </button>
          <p className="mt-2 text-center text-xs text-neutral-500">
            Immich のゴミ箱で30日間復元できます(完全削除はしません)
          </p>
        </div>
      )}
      <Toast toast={toast} onHide={hideToast} />
    </div>
  );
}
