import { useEffect, useState } from 'react';
import { api, type Settings as SettingsData } from '../api';
import { Toast, useToast } from '../components/Toast';

interface NumField {
  key: keyof Omit<SettingsData, 'device_resolutions'>;
  label: string;
  hint: string;
  step?: number;
}

const FIELDS: { section: string; items: NumField[] }[] = [
  {
    section: '📱 スクショ',
    items: [
      { key: 'screenshot_threshold', label: '判定しきい値', hint: '0〜1。下げるほど広く拾う', step: 0.05 },
      { key: 'screenshot_min_age_days', label: '候補に入れるまでの日数', hint: '0 = すぐ候補。30 なら撮影後30日は候補にしない' },
    ],
  },
  {
    section: '📄 メモ写真',
    items: [
      { key: 'memo_threshold', label: '判定しきい値', hint: '0〜1', step: 0.05 },
      { key: 'memo_age_days', label: '賞味期限の日数', hint: 'この日数を過ぎたメモをより候補にしやすくする' },
    ],
  },
  {
    section: '🌫 ぼやけ / 🔁 グループ',
    items: [
      { key: 'blur_threshold', label: 'ぼやけしきい値', hint: 'シャープネスがこの値未満で候補。上げるほど広く拾う' },
      { key: 'similar_hamming', label: '類似の距離しきい値', hint: '0〜64。上げるほど「似てる」判定が緩くなる' },
      { key: 'burst_gap_seconds', label: '連写の間隔(秒)', hint: 'この秒数以内の連続撮影を連写とみなす' },
    ],
  },
  {
    section: '🎞 動画',
    items: [{ key: 'video_large_mb', label: '大きい動画のしきい値(MB)', hint: 'このサイズ以上の動画を「大きい動画」候補に' }],
  },
  {
    section: '🌙 自動実行',
    items: [{ key: 'auto_scan_hour', label: '自動スキャンの時刻', hint: '0〜23時。-1 で無効。実行前にDBを自動バックアップ' }],
  },
];

// SPEC S-5: 設定。変更 → 保存 → 再スキャンで反映
export function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [resText, setResText] = useState('');
  const [busy, setBusy] = useState(false);
  const { toast, showToast, hideToast } = useToast();

  useEffect(() => {
    api.getSettings().then((s) => {
      setSettings(s);
      setResText(s.device_resolutions.join('\n'));
    });
  }, []);

  async function save(rescan: boolean) {
    if (!settings) return;
    setBusy(true);
    try {
      const device_resolutions = resText
        .split(/[\n,]/)
        .map((s) => s.trim())
        .filter((s) => /^\d+x\d+$/.test(s));
      await api.putSettings({ ...settings, device_resolutions });
      if (rescan) {
        const r = await api.scan();
        showToast(`保存して再スキャンしました(スクショ${r.screenshots} メモ${r.memo} ぼやけ${r.blurry})`, { ms: 5000 });
      } else {
        showToast('保存しました(反映には再スキャン)');
      }
    } catch {
      showToast('保存に失敗しました', { ms: 4000 });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 pb-28 pt-4">
      <header className="mb-5 flex items-center gap-3">
        <a href="#/" className="text-neutral-400">←</a>
        <h1 className="font-bold">設定</h1>
      </header>

      {!settings ? (
        <p className="text-center text-neutral-500">読み込み中…</p>
      ) : (
        <div className="flex flex-col gap-6">
          {FIELDS.map((sec) => (
            <section key={sec.section}>
              <h2 className="mb-2 text-sm font-medium text-neutral-400">{sec.section}</h2>
              <div className="flex flex-col gap-3 rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
                {sec.items.map((f) => (
                  <label key={f.key} className="flex items-center justify-between gap-3 text-sm">
                    <span>
                      {f.label}
                      <span className="block text-[11px] text-neutral-500">{f.hint}</span>
                    </span>
                    <input
                      type="number"
                      step={f.step ?? 1}
                      value={settings[f.key]}
                      onChange={(e) => setSettings({ ...settings, [f.key]: Number(e.target.value) })}
                      className="w-24 shrink-0 rounded-lg border border-neutral-700 bg-neutral-950 px-2 py-1.5 text-right"
                    />
                  </label>
                ))}
              </div>
            </section>
          ))}

          <section>
            <h2 className="mb-2 text-sm font-medium text-neutral-400">端末の画面解像度(スクショ判定用)</h2>
            <textarea
              value={resText}
              onChange={(e) => setResText(e.target.value)}
              rows={5}
              placeholder="1179x2556(1行に1つ)"
              className="w-full rounded-2xl border border-neutral-800 bg-neutral-900 p-3 font-mono text-xs"
            />
            <p className="mt-1 text-[11px] text-neutral-500">お使いのスマホの解像度だけに絞ると精度が上がります</p>
          </section>
        </div>
      )}

      {settings && (
        <div className="fixed bottom-0 left-1/2 w-[min(100%,28rem)] -translate-x-1/2 bg-gradient-to-t from-neutral-950 via-neutral-950/95 to-transparent px-4 pb-6 pt-8">
          <div className="flex gap-2">
            <button
              onClick={() => save(false)}
              disabled={busy}
              className="flex-1 rounded-2xl border border-neutral-600 py-3 text-sm font-bold disabled:opacity-50"
            >
              保存
            </button>
            <button
              onClick={() => save(true)}
              disabled={busy}
              className="flex-1 rounded-2xl bg-neutral-200 py-3 text-sm font-bold text-neutral-900 disabled:opacity-50"
            >
              {busy ? '実行中…' : '保存して再スキャン'}
            </button>
          </div>
        </div>
      )}
      <Toast toast={toast} onHide={hideToast} />
    </div>
  );
}
