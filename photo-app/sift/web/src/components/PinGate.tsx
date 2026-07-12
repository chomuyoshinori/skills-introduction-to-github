import { useState } from 'react';
import { api } from '../api';

// SPEC §11 の簡易PINロック(サーバーで SIFT_PIN 設定時のみ表示される)
export function PinGate({ onOk }: { onOk: () => void }) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!pin) return;
    setBusy(true);
    setError(false);
    try {
      await api.login(pin);
      onOk();
    } catch {
      setError(true);
      setPin('');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-8">
      <div className="text-4xl">🔒</div>
      <h1 className="font-bold">Sift</h1>
      <p className="text-sm text-neutral-400">PIN を入力してください</p>
      <form onSubmit={submit} className="flex w-full max-w-60 flex-col gap-3">
        <input
          type="password"
          inputMode="numeric"
          autoFocus
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          className={`rounded-xl border bg-neutral-900 px-4 py-3 text-center text-xl tracking-widest ${
            error ? 'border-red-500' : 'border-neutral-700'
          }`}
        />
        {error && <p className="text-center text-xs text-red-400">PIN が違います</p>}
        <button
          type="submit"
          disabled={busy || !pin}
          className="rounded-xl bg-neutral-200 py-3 font-bold text-neutral-900 disabled:opacity-50"
        >
          解除
        </button>
      </form>
    </div>
  );
}
