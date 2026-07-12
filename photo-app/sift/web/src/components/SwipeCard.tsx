import { useRef, useState } from 'react';
import { thumbUrl, type AssetItem } from '../api';

export type Dir = 'left' | 'right' | 'up' | 'down';

const FLY: Record<Dir, { x: number; y: number; rot: number }> = {
  left: { x: -600, y: 0, rot: -20 },
  right: { x: 600, y: 0, rot: 20 },
  up: { x: 0, y: -800, rot: 0 },
  down: { x: 0, y: 800, rot: 0 },
};

// SPEC S-2: ←削除予定 / →残す / ↑お気に入り / ↓あとで
export function SwipeCard({
  item,
  onDecide,
  onTap,
}: {
  item: AssetItem;
  onDecide: (dir: Dir) => void;
  onTap: () => void;
}) {
  const [drag, setDrag] = useState({ dx: 0, dy: 0, active: false });
  const [fly, setFly] = useState<Dir | null>(null);
  const start = useRef<{ x: number; y: number } | null>(null);
  const dragRef = useRef({ dx: 0, dy: 0 });

  function release(dir: Dir) {
    setFly(dir);
    window.setTimeout(() => onDecide(dir), 180);
  }

  function onPointerDown(e: React.PointerEvent<HTMLDivElement>) {
    if (fly) return;
    start.current = { x: e.clientX, y: e.clientY };
    dragRef.current = { dx: 0, dy: 0 };
    (e.currentTarget as HTMLDivElement).setPointerCapture(e.pointerId);
    setDrag({ dx: 0, dy: 0, active: true });
  }

  function onPointerMove(e: React.PointerEvent<HTMLDivElement>) {
    if (!start.current || fly) return;
    const dx = e.clientX - start.current.x;
    const dy = e.clientY - start.current.y;
    dragRef.current = { dx, dy };
    setDrag({ dx, dy, active: true });
  }

  function onPointerUp() {
    if (!start.current || fly) return;
    const { dx, dy } = dragRef.current;
    start.current = null;
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) {
      setDrag({ dx: 0, dy: 0, active: false });
      onTap();
      return;
    }
    if (Math.abs(dx) >= Math.abs(dy) && Math.abs(dx) > 90) {
      release(dx < 0 ? 'left' : 'right');
    } else if (Math.abs(dy) > 80) {
      release(dy < 0 ? 'up' : 'down');
    } else {
      setDrag({ dx: 0, dy: 0, active: false });
    }
  }

  const t = fly
    ? `translate(${FLY[fly].x}px, ${FLY[fly].y}px) rotate(${FLY[fly].rot}deg)`
    : `translate(${drag.dx}px, ${drag.dy}px) rotate(${drag.dx / 20}deg)`;
  const opacity = (v: number) => Math.min(1, Math.max(0, v));

  return (
    <div
      className="absolute inset-0 flex touch-none select-none flex-col items-center justify-center"
      style={{
        transform: t,
        transition: drag.active && !fly ? 'none' : 'transform 0.18s ease-out',
        cursor: 'grab',
      }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
    >
      <div className="relative flex max-h-full max-w-full items-center justify-center overflow-hidden rounded-2xl bg-neutral-900 shadow-xl shadow-black/50">
        <img
          src={thumbUrl(item.id, 'preview')}
          alt={item.fileName ?? ''}
          className="max-h-[62vh] max-w-full object-contain"
          draggable={false}
        />
        {/* ドラッグ方向のオーバーレイラベル(SPEC §8.3: 削除はグレー、赤を使わない) */}
        <Overlay show={opacity(-drag.dx / 120)} pos="left-4 top-4" cls="border-neutral-400 text-neutral-200" label="🗑 削除予定" />
        <Overlay show={opacity(drag.dx / 120)} pos="right-4 top-4" cls="border-emerald-400 text-emerald-300" label="✓ 残す" />
        <Overlay show={opacity(-drag.dy / 100)} pos="left-1/2 top-4 -translate-x-1/2" cls="border-pink-400 text-pink-300" label="♡ お気に入り" />
        <Overlay show={opacity(drag.dy / 100)} pos="left-1/2 bottom-4 -translate-x-1/2" cls="border-sky-400 text-sky-300" label="→ あとで" />
      </div>
    </div>
  );
}

function Overlay({ show, pos, cls, label }: { show: number; pos: string; cls: string; label: string }) {
  return (
    <div
      className={`pointer-events-none absolute ${pos} rounded-lg border-2 px-3 py-1 text-lg font-bold ${cls}`}
      style={{ opacity: show }}
    >
      {label}
    </div>
  );
}
