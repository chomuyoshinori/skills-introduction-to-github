import { useEffect, useState } from 'react';
import { api, fmtBytes, fmtDate, thumbUrl, type Group } from '../api';
import { Toast, useToast } from '../components/Toast';

const KIND_LABEL: Record<string, { label: string; cls: string }> = {
  duplicate: { label: '完全重複', cls: 'text-amber-300' },
  burst: { label: '連写', cls: 'text-sky-300' },
  similar: { label: '類似', cls: 'text-violet-300' },
};

// SPEC S-3: グループ単位で1判断。★=残す(自動提案)、タップで変更、拡大比較あり
export function Groups() {
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [best, setBest] = useState<Record<number, string>>({});
  const [compare, setCompare] = useState<Group | null>(null);
  const { toast, showToast, hideToast } = useToast();

  const load = () => {
    api.groups().then((r) => {
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
        <h1 className="font-bold">重複・類似の比較 {groups && `(残り ${groups.length}組)`}</h1>
      </header>

      {groups === null && <p className="text-center text-neutral-500">読み込み中…</p>}
      {groups !== null && groups.length === 0 && (
        <p className="mt-16 text-center text-neutral-400">重複・類似はありません 🎉</p>
      )}

      <div className="flex flex-col gap-6">
        {groups?.map((g) => {
          const kind = KIND_LABEL[g.kind] ?? { label: g.kind, cls: 'text-neutral-300' };
          const potential = g.assets
            .filter((a) => a.id !== best[g.id] && (a.decision === null || a.decision === 'later'))
            .reduce((s, a) => s + a.sizeBytes, 0);
          return (
            <section key={g.id} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
              <h2 className="mb-3 flex items-center gap-2 text-sm text-neutral-300">
                <span className={`rounded bg-neutral-800 px-1.5 py-0.5 text-xs font-bold ${kind.cls}`}>{kind.label}</span>
                {fmtDate(g.assets[0]?.takenAt)}・{g.assets.length}枚
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
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => keepBest(g)}
                  className="flex-1 rounded-full bg-neutral-200 py-2 text-sm font-bold text-neutral-900"
                >
                  ★以外を削除予定へ(+{fmtBytes(potential)})
                </button>
                <button onClick={() => keepAll(g)} className="rounded-full border border-neutral-600 px-4 py-2 text-sm">
                  全部残す
                </button>
                <button onClick={() => setCompare(g)} className="rounded-full border border-neutral-600 px-4 py-2 text-sm">
                  🔍 拡大比較
                </button>
              </div>
            </section>
          );
        })}
      </div>

      {compare && (
        <CompareModal
          group={compare}
          bestId={best[compare.id]}
          onPickBest={(id) => setBest((b) => ({ ...b, [compare.id]: id }))}
          onClose={() => setCompare(null)}
        />
      )}
      <Toast toast={toast} onHide={hideToast} />
    </div>
  );
}

// SPEC S-3 の A/B 比較(Phase 2 版): ★と比較対象を並べ、切り替えながら★を選び直す
function CompareModal({
  group,
  bestId,
  onPickBest,
  onClose,
}: {
  group: Group;
  bestId: string;
  onPickBest: (id: string) => void;
  onClose: () => void;
}) {
  const [i, setI] = useState(0);
  const bestAsset = group.assets.find((a) => a.id === bestId);
  const others = group.assets.filter((a) => a.id !== bestId);
  const ch = others[((i % others.length) + others.length) % others.length];
  if (!bestAsset || !ch) return null;

  const cell = (a: typeof bestAsset, tag: string, tagCls: string) => (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className={`mb-1 text-center text-xs font-bold ${tagCls}`}>{tag}</div>
      <div className="flex min-h-0 flex-1 items-center justify-center overflow-hidden rounded-xl bg-neutral-900">
        <img src={thumbUrl(a.id, 'preview')} alt="" className="max-h-full max-w-full object-contain" />
      </div>
      <div className="mt-1 text-center text-[11px] text-neutral-400">
        {fmtBytes(a.sizeBytes)}
        {a.sharpness != null && <> ・ 鮮明度 {Math.round(a.sharpness)}</>}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/95 p-4">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-bold">拡大比較</span>
        <button onClick={onClose} className="rounded-full px-3 py-1 text-neutral-400">✕ 閉じる</button>
      </div>
      <div className="flex min-h-0 flex-1 gap-2">
        {cell(bestAsset, '★ 残す予定', 'text-amber-300')}
        {cell(ch, '比較対象', 'text-neutral-300')}
      </div>
      <div className="mt-3 flex items-center justify-center gap-3">
        {others.length > 1 && (
          <button onClick={() => setI((x) => x - 1)} className="h-11 w-11 rounded-full border border-neutral-600">‹</button>
        )}
        <button
          onClick={() => onPickBest(ch.id)}
          className="rounded-full bg-neutral-200 px-5 py-2.5 text-sm font-bold text-neutral-900"
        >
          比較対象を★にする
        </button>
        {others.length > 1 && (
          <button onClick={() => setI((x) => x + 1)} className="h-11 w-11 rounded-full border border-neutral-600">›</button>
        )}
      </div>
    </div>
  );
}
