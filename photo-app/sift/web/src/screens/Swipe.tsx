import { useEffect, useRef, useState } from 'react';
import { api, fmtBytes, fmtDate, thumbUrl, type AssetItem, type Decision } from '../api';
import { SwipeCard, type Dir } from '../components/SwipeCard';
import { Toast, useToast } from '../components/Toast';

const DIR_TO_DECISION: Record<Dir, { decision: Decision; label: string }> = {
  left: { decision: 'trash_pending', label: '削除予定' },
  right: { decision: 'keep', label: '残す' },
  up: { decision: 'favorite', label: 'お気に入り' },
  down: { decision: 'later', label: 'あとで' },
};

const CATEGORY_LABEL: Record<string, string> = { screenshot: 'スクショ' };

// SPEC S-2: 1画面1判断のスワイプ選別。50枚で1セッション
export function Swipe({ category }: { category: string }) {
  const [items, setItems] = useState<AssetItem[] | null>(null);
  const [idx, setIdx] = useState(0);
  const [freed, setFreed] = useState(0);
  const [zoom, setZoom] = useState(false);
  const historyRef = useRef<{ item: AssetItem; dir: Dir; index: number }[]>([]);
  // 判断とUndoのAPI呼び出しは直列化する(順序が入れ替わるとUndoがずれる)
  const chainRef = useRef<Promise<unknown>>(Promise.resolve());
  const { toast, showToast, hideToast } = useToast();

  const load = () => {
    setItems(null);
    setIdx(0);
    setFreed(0);
    historyRef.current = [];
    api.queueItems(category).then((r) => setItems(r.items)).catch(() => showToast('読み込みに失敗しました'));
  };
  useEffect(load, [category]);

  function decide(dir: Dir) {
    if (!items || idx >= items.length) return;
    const item = items[idx];
    historyRef.current.push({ item, dir, index: idx });
    chainRef.current = chainRef.current
      .then(() => api.decide([item.id], DIR_TO_DECISION[dir].decision))
      .catch(console.error);
    if (dir === 'left') setFreed((f) => f + item.sizeBytes);
    setIdx((i) => i + 1);
    showToast(`「${DIR_TO_DECISION[dir].label}」にしました`, { action: '元に戻す', onAction: undo, ms: 3000 });
  }

  function undo() {
    const last = historyRef.current.pop();
    if (!last) return;
    chainRef.current = chainRef.current.then(() => api.undo()).catch(console.error);
    if (last.dir === 'left') setFreed((f) => Math.max(0, f - last.item.sizeBytes));
    setIdx(last.index);
  }

  const current = items && idx < items.length ? items[idx] : null;
  const next = items && idx + 1 < items.length ? items[idx + 1] : null;

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between px-4 py-3 text-sm">
        <a href="#/" className="rounded-full px-2 py-1 text-neutral-400">✕ 閉じる</a>
        <span className="font-bold">{CATEGORY_LABEL[category] ?? category}</span>
        <span className="text-neutral-400">
          {items ? `${Math.min(idx + 1, items.length)}/${items.length}` : '…'}{' '}
          <span className="text-neutral-200">+{fmtBytes(freed)} 🗑</span>
        </span>
      </header>

      <main className="relative flex-1 overflow-hidden px-6">
        {items === null && <p className="mt-20 text-center text-neutral-500">読み込み中…</p>}
        {items !== null && !current && <Done freed={freed} onMore={load} anyLeft={items.length > 0} />}
        {next && (
          <div className="absolute inset-0 flex scale-95 items-center justify-center opacity-40">
            <img src={thumbUrl(next.id, 'preview')} alt="" className="max-h-[62vh] max-w-full rounded-2xl object-contain" />
          </div>
        )}
        {current && <SwipeCard key={current.id} item={current} onDecide={decide} onTap={() => setZoom(true)} />}
      </main>

      {current && (
        <div className="px-4 pb-1 text-center text-xs text-neutral-500">
          {fmtDate(current.takenAt)} ・ {current.fileName} ・ {fmtBytes(current.sizeBytes)}
        </div>
      )}

      <footer className="flex items-center justify-center gap-5 px-4 pb-8 pt-3">
        <ActionBtn label="削除予定" onClick={() => decide('left')} disabled={!current}>🗑</ActionBtn>
        <ActionBtn label="元に戻す" small onClick={undo} disabled={historyRef.current.length === 0}>↩︎</ActionBtn>
        <ActionBtn label="あとで" small onClick={() => decide('down')} disabled={!current}>⏬</ActionBtn>
        <ActionBtn label="お気に入り" small onClick={() => decide('up')} disabled={!current}>♡</ActionBtn>
        <ActionBtn label="残す" onClick={() => decide('right')} disabled={!current} accent>✓</ActionBtn>
      </footer>

      {zoom && current && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/95" onClick={() => setZoom(false)}>
          <img src={thumbUrl(current.id, 'preview')} alt="" className="max-h-full max-w-full object-contain" />
        </div>
      )}
      <Toast toast={toast} onHide={hideToast} />
    </div>
  );
}

function ActionBtn({
  children,
  label,
  onClick,
  disabled,
  small,
  accent,
}: {
  children: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  small?: boolean;
  accent?: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-1">
      <button
        onClick={onClick}
        disabled={disabled}
        aria-label={label}
        className={`flex items-center justify-center rounded-full border disabled:opacity-30 ${
          small ? 'h-11 w-11 text-lg' : 'h-14 w-14 text-2xl'
        } ${accent ? 'border-emerald-500 text-emerald-400' : 'border-neutral-600 text-neutral-300'}`}
      >
        {children}
      </button>
      <span className="text-[10px] text-neutral-500">{label}</span>
    </div>
  );
}

// SPEC S-2: セッション完了画面
function Done({ freed, onMore, anyLeft }: { freed: number; onMore: () => void; anyLeft: boolean }) {
  return (
    <div className="mt-20 flex flex-col items-center gap-4 text-center">
      <div className="text-4xl">🎉</div>
      <p className="font-bold">
        {anyLeft ? 'このセッションは完了!' : 'このカテゴリの候補はありません'}
      </p>
      {freed > 0 && <p className="text-sm text-neutral-400">+{fmtBytes(freed)} 解放予定になりました</p>}
      <p className="max-w-xs text-xs text-neutral-500">
        削除予定はまだ実行されていません。ホームの「確認して実行」からゴミ箱へ移動できます。
      </p>
      <div className="mt-2 flex gap-3">
        {anyLeft && (
          <button onClick={onMore} className="rounded-full border border-neutral-600 px-5 py-2 text-sm">
            続ける
          </button>
        )}
        <a href="#/" className="rounded-full bg-neutral-200 px-5 py-2 text-sm font-bold text-neutral-900">
          ホームへ
        </a>
      </div>
    </div>
  );
}
