import { useEffect, useState } from 'react';
import { api, fmtBytes, type Stats as StatsData } from '../api';

// SPEC S-5(F-9): 統計。数字は「解放できた容量」を主役にする
export function Stats() {
  const [stats, setStats] = useState<StatsData | null>(null);
  useEffect(() => {
    api.stats().then(setStats);
  }, []);

  const maxMonthly = Math.max(1, ...(stats?.monthlyFreed.map((m) => m.bytes) ?? [1]));

  return (
    <div className="mx-auto max-w-md px-4 pb-16 pt-4">
      <header className="mb-5 flex items-center gap-3">
        <a href="#/" className="text-neutral-400">←</a>
        <h1 className="font-bold">統計</h1>
      </header>

      {!stats ? (
        <p className="text-center text-neutral-500">読み込み中…</p>
      ) : (
        <>
          <div className="mb-6 rounded-2xl border border-neutral-800 bg-neutral-900 p-5 text-center">
            <div className="text-sm text-neutral-400">これまでに解放した容量</div>
            <div className="mt-1 text-4xl font-bold text-emerald-400">{fmtBytes(stats.freedBytes)}</div>
            <div className="mt-2 text-xs text-neutral-500">
              ゴミ箱へ {stats.trashedCount}枚 ・ レビュー済み {stats.reviewedCount}枚
            </div>
          </div>

          <h2 className="mb-2 text-sm font-medium text-neutral-400">残っている候補</h2>
          <div className="mb-6 grid grid-cols-2 gap-2 text-sm">
            <RemainRow label="📱 スクショ" value={`${stats.remaining.screenshot}枚`} />
            <RemainRow label="📄 メモ写真" value={`${stats.remaining.memo}枚`} />
            <RemainRow label="🌫 ぼやけ" value={`${stats.remaining.blurry}枚`} />
            <RemainRow label="🔁 重複・類似" value={`${stats.remaining.groups}組`} />
          </div>

          {stats.monthlyFreed.length > 0 && (
            <>
              <h2 className="mb-2 text-sm font-medium text-neutral-400">月別の解放実績</h2>
              <div className="flex flex-col gap-2">
                {stats.monthlyFreed.map((m) => (
                  <div key={m.month} className="flex items-center gap-2 text-xs">
                    <span className="w-16 shrink-0 text-neutral-400">{m.month}</span>
                    <div className="h-4 flex-1 overflow-hidden rounded bg-neutral-900">
                      <div
                        className="h-full rounded bg-emerald-700"
                        style={{ width: `${Math.max(4, (m.bytes / maxMonthly) * 100)}%` }}
                      />
                    </div>
                    <span className="w-20 shrink-0 text-right text-neutral-300">
                      {fmtBytes(m.bytes)}({m.count})
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function RemainRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-900 px-3 py-2.5">
      <span className="text-neutral-300">{label}</span>
      <span className="font-bold">{value}</span>
    </div>
  );
}
