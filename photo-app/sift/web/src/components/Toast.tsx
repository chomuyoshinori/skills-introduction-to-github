import { useRef, useState } from 'react';

export interface ToastState {
  msg: string;
  action?: string;
  onAction?: () => void;
}

export function useToast() {
  const [toast, setToast] = useState<ToastState | null>(null);
  const timer = useRef<number | undefined>(undefined);

  function showToast(msg: string, opts: { action?: string; onAction?: () => void; ms?: number } = {}) {
    setToast({ msg, action: opts.action, onAction: opts.onAction });
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setToast(null), opts.ms ?? 2500);
  }

  return { toast, showToast, hideToast: () => setToast(null) };
}

export function Toast({ toast, onHide }: { toast: ToastState | null; onHide: () => void }) {
  if (!toast) return null;
  return (
    <div className="fixed bottom-24 left-1/2 z-50 -translate-x-1/2">
      <div className="flex items-center gap-3 rounded-full bg-neutral-800 px-4 py-2 text-sm text-neutral-200 shadow-lg shadow-black/40">
        <span>{toast.msg}</span>
        {toast.action && (
          <button
            className="font-bold text-sky-400"
            onClick={() => {
              toast.onAction?.();
              onHide();
            }}
          >
            {toast.action}
          </button>
        )}
      </div>
    </div>
  );
}
