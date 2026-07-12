import { useEffect, useState } from 'react';
import { api, fmtBytes, fmtDate, thumbUrl, type Group } from '../api';
import { Toast, useToast } from '../components/Toast';

// SPEC S-3(Phase 1 版): 重複グループはグループ単位で1判断。
// ★=残す1枚(自動提案)。タップで★を移せる。
export function Duplicates() {
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [best, setBest] = useState<Record<number, string>>({});
  const { toast, showToast, hideToast } = useToast();

  const load = () => {
    api.groups('duplicate').then((r) => {
      setGroups(r.groups);
      setBest(Object.fromEntries(r.groups.map((g) => [g.id, g.bestAssetId ?? g.assets[0]?.id])));
    });
  };
  useEffect(load, []);

  async function keepBest(g: Group) {
    const r = await api.keepBest(g.id, best[g.id]);
    setGroups((gs) => gs?.filter((x) => x.id !== g.id) ?? null);
    showToast(`${r.trashed}枚を削除予定にしました`, {
      action: '元に戻す',
      onAction: async () => {
        await api.undo();
        load();
      },
      ms: 4000,
    });
  }

  async function keepAll(g: Group) {
    const undecided = g.assets.filter((a) => a.decision === null || a.decision === 'later');
    await api.decide(undecided.map((a) => a.id), 'keep');
    setGroups((gs) => gs?.filter((x) => x.id !== g.id) ?? null);
    showToast('全部残しました', {
      action: '元に戻す',
      onAction: async () => {
        await api.undo();
        load();
      },
      ms: 4000,
    });
  }

  return (
    <div className="mx-auto max-w-md px-4 pb-16 pt-4">
      <header className="mb-4 flex items-center gap-3">
        <a href="#/" className="text-neutral-400">←</a>
        <h1 className="font-bold">重複の比較 {groups && `(残り ${groups.length}組)`}</h1>
      </header>

      {groups === null && <p className="text-center text-neutral-500">読み込み中…</p>}
      {groups !== null && groups.length === 0 && (
        <p className="mt-16 text-center text-neutral-400">重複はありません 🎉</p>
      )}

      <div className="flex flex-col gap-6">
        {groups?.map((g) => {
          const potential = g.assets
            .filter((a) => a.id !== best[g.id] && (a.decision === null || a.decision === 'later'))
            .reduce((s, a) => s + a.sizeBytes, 0);
          return (
            <section key={g.id} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
              <h2 className="mb-3 text-sm text-neutral-300">
                {fmtDate(g.assets[0]?.takenAt)} の同じ写真 {g.assets.length}枚
              </h2>
              <div className="flex gap-2 overflow-x-auto pb-2">
                {g.assets.map((a) => {
                  const isBest = best[g.id] === a.id;
                  return (
                    <button
                      key={a.id}
                      onClick={() => setBest((b) => ({ ...b, [g.id]: a.id }))}
                      className={`relative shrink-0 overflow-hidden rounded-xl border-2 ${
                        isBest ? 'border-amber-400' : 'border-transparent opacity-80'
                      }`}
                    >
                      <img src={thumbUrl(a.id)} alt="" className="h-32 w-32 object-cover" draggable={false} />
                      {isBest && (
                        <span className="absolute left-1 top-1 rounded bg-amber-400 px-1.5 py-0.5 text-xs font-bold text-black">
                          ★ 残す
                        </span>
                      )}
                      <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1 text-[10px]">
                        {fmtBytes(a.sizeBytes)}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="mb-3 mt-1 text-xs text-neutral-500">タップで残す1枚(★)を変更できます</p>
              <div className="flex gap-2">
                <button
                  onClick={() => keepBest(g)}
                  className="flex-1 rounded-full bg-neutral-200 py-2 text-sm font-bold text-neutral-900"
                >
                  ★以外を削除予定へ(+{fmtBytes(potential)})
                </button>
                <button onClick={() => keepAll(g)} className="rounded-full border border-neutral-600 px-4 py-2 text-sm">
                  全部残す
                </button>
              </div>
            </section>
          );
        })}
      </div>
      <Toast toast={toast} onHide={hideToast} />
    </div>
  );
}
