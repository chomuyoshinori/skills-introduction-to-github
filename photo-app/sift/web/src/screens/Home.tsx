import { useEffect, useState } from 'react';
import { api, fmtBytes, type QueuesRes, type Stats } from '../api';
import { Toast, useToast } from '../components/Toast';

// SPEC S-1: 今日の整理提案。カテゴリカードに枚数+概算容量を必ず併記
export function Home() {
  const [queues, setQueues] = useState<QueuesRes | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [scanning, setScanning] = useState(false);
  const { toast, showToast, hideToast } = useToast();

  const load = () => {
    api.queues().then(setQueues).catch(() => showToast('サーバーに接続できません'));
    api.stats().then(setStats).catch(() => {});
  };
  useEffect(load, []);

  async function scan() {
    setScanning(true);
    try {
      const r = await api.scan();
      showToast(`スキャン完了: ${r.scanned}枚 / スクショ${r.screenshots}枚 / 重複${r.duplicateGroups}組`, { ms: 4000 });
      load();
    } catch {
      showToast('スキャンに失敗しました(Immich接続を確認)', { ms: 4000 });
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col px-4 pb-32 pt-6">
      <header className="mb-6 flex items-baseline justify-between">
        <h1 className="text-2xl font-bold tracking-wide">Sift</h1>
        {stats && stats.freedBytes > 0 && (
          <span className="text-sm text-emerald-400">解放済み {fmtBytes(stats.freedBytes)} 🎉</span>
        )}
      </header>

      <h2 className="mb-3 text-sm font-medium text-neutral-400">今日の整理提案</h2>
      <div className="grid grid-cols-2 gap-3">
        <Card
          emoji="📱"
          title="スクショ"
          detail={queues ? `${queues.screenshot.count}枚 ≈${fmtBytes(queues.screenshot.bytes)}` : '…'}
          href="#/swipe/screenshot"
          cta="整理する →"
          disabled={!queues || queues.screenshot.count === 0}
        />
        <Card
          emoji="🔁"
          title="重複"
          detail={queues ? `${queues.duplicates.groups}組 ≈${fmtBytes(queues.duplicates.bytes)}` : '…'}
          href="#/duplicates"
          cta="比較する →"
          disabled={!queues || queues.duplicates.groups === 0}
        />
        <Card emoji="📄" title="メモ写真" detail="Phase 2 で対応" disabled />
        <Card emoji="🌫" title="ぼやけ" detail="Phase 2 で対応" disabled />
      </div>

      <button
        onClick={scan}
        disabled={scanning}
        className="mt-6 self-center rounded-full border border-neutral-700 px-4 py-2 text-sm text-neutral-400 disabled:opacity-50"
      >
        {scanning ? 'スキャン中…' : '候補を再スキャン'}
      </button>

      {stats && (
        <p className="mt-4 self-center text-xs text-neutral-600">
          これまでにレビュー {stats.reviewedCount}枚 / ゴミ箱へ {stats.trashedCount}枚
        </p>
      )}

      {queues && queues.trashPending.count > 0 && (
        <a
          href="#/trash"
          className="fixed bottom-6 left-1/2 flex w-[min(92%,28rem)] -translate-x-1/2 items-center justify-between rounded-2xl bg-neutral-800 px-5 py-4 shadow-lg shadow-black/50"
        >
          <span className="text-sm">
            🗑 削除予定 <b>{queues.trashPending.count}枚</b> ≈{fmtBytes(queues.trashPending.bytes)}
          </span>
          <span className="rounded-full bg-neutral-200 px-3 py-1 text-sm font-bold text-neutral-900">確認して実行</span>
        </a>
      )}
      <Toast toast={toast} onHide={hideToast} />
    </div>
  );
}

function Card({
  emoji,
  title,
  detail,
  href,
  cta,
  disabled,
}: {
  emoji: string;
  title: string;
  detail: string;
  href?: string;
  cta?: string;
  disabled?: boolean;
}) {
  const body = (
    <div
      className={`flex h-32 flex-col justify-between rounded-2xl border border-neutral-800 bg-neutral-900 p-4 ${
        disabled ? 'opacity-45' : 'active:scale-[0.98]'
      }`}
    >
      <div className="text-2xl">{emoji}</div>
      <div>
        <div className="font-bold">{title}</div>
        <div className="text-xs text-neutral-400">{detail}</div>
        {cta && !disabled && <div className="mt-1 text-xs font-bold text-sky-400">{cta}</div>}
      </div>
    </div>
  );
  return disabled || !href ? body : <a href={href}>{body}</a>;
}
