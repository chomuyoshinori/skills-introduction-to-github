import type { DuplicateGroup, ImmichAsset, ImmichClient, Thumb } from './types';

// ─────────────────────────────────────────────────────────────
// Immich なしで UI/選別フローを試すためのモック(SIFT_MOCK=1)。
// スクショ24枚・重複5組・通常写真40枚のダミーライブラリを生成する。
// ─────────────────────────────────────────────────────────────

// 乱数は再現性のためシード付き LCG
function lcg(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 2 ** 32;
  };
}

interface MockAsset extends ImmichAsset {
  hue: number;
  label: string;
  portrait: boolean;
}

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

function buildLibrary(): { assets: MockAsset[]; duplicates: DuplicateGroup[] } {
  const rand = lcg(20260712);
  const assets: MockAsset[] = [];
  const duplicates: DuplicateGroup[] = [];
  // 撮影日は 2026-06-20 から過去へ分散させる(決め打ちで再現性を保つ)
  const date = (daysAgo: number, h: number, m: number, s: number) => {
    const base = Date.UTC(2026, 5, 20, h, m, s);
    return new Date(base - daysAgo * 86400_000).toISOString();
  };

  // スクリーンショット 24枚(PNG・EXIFなし・iPhone画面解像度)
  for (let i = 0; i < 24; i++) {
    const d = Math.floor(rand() * 170);
    const taken = date(d, 9 + (i % 12), (i * 7) % 60, (i * 13) % 60);
    assets.push({
      id: `mock-shot-${i}`,
      originalFileName: `Screenshot_${taken.slice(0, 10)}-${pad(i)}.png`,
      originalMimeType: 'image/png',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: false,
      type: 'IMAGE',
      exifInfo: {
        fileSizeInByte: Math.round((0.8 + rand() * 2.7) * 1_000_000),
        exifImageWidth: 1179,
        exifImageHeight: 2556,
      },
      hue: 210,
      label: `スクショ #${i + 1}`,
      portrait: true,
    });
  }

  // 重複グループ 5組(2〜3枚、同色サムネで「同じ写真」感を出す)
  for (let g = 0; g < 5; g++) {
    const n = g % 2 === 0 ? 2 : 3;
    const hue = Math.floor(rand() * 360);
    const taken = date(10 + g * 9, 14, g * 11, 0);
    const members: MockAsset[] = [];
    for (let k = 0; k < n; k++) {
      members.push({
        id: `mock-dup-${g}-${k}`,
        originalFileName: `IMG_${4100 + g * 10 + k}.JPG`,
        originalMimeType: 'image/jpeg',
        fileCreatedAt: taken,
        localDateTime: taken,
        isFavorite: false,
        type: 'IMAGE',
        exifInfo: {
          make: 'Apple',
          model: 'iPhone 15 Pro',
          fileSizeInByte: Math.round((3 + k * 1.4 + rand()) * 1_000_000),
          exifImageWidth: 4032,
          exifImageHeight: 3024,
        },
        hue,
        label: `重複${g + 1} - ${String.fromCharCode(65 + k)}`,
        portrait: false,
      });
    }
    assets.push(...members);
    duplicates.push({ duplicateId: `mock-dupgroup-${g}`, assets: members });
  }

  // 通常写真 40枚(うち2枚はお気に入り → 候補から除外されることの確認用)
  for (let i = 0; i < 40; i++) {
    const d = Math.floor(rand() * 300);
    const taken = date(d, 8 + (i % 10), (i * 3) % 60, (i * 17) % 60);
    assets.push({
      id: `mock-photo-${i}`,
      originalFileName: `IMG_${5200 + i}.JPG`,
      originalMimeType: 'image/jpeg',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: i === 3 || i === 17,
      type: 'IMAGE',
      exifInfo: {
        make: 'Apple',
        model: 'iPhone 15 Pro',
        fileSizeInByte: Math.round((2.5 + rand() * 5.5) * 1_000_000),
        exifImageWidth: 4032,
        exifImageHeight: 3024,
      },
      hue: Math.floor(rand() * 360),
      label: `写真 #${i + 1}`,
      portrait: rand() < 0.3,
    });
  }

  return { assets, duplicates };
}

function thumbnailSvg(a: MockAsset, size: 'thumbnail' | 'preview'): string {
  const w = a.portrait ? 360 : 640;
  const h = a.portrait ? 780 : 480;
  const scale = size === 'thumbnail' ? 0.5 : 1;
  const isShot = a.id.startsWith('mock-shot');
  const bg = isShot ? '#111827' : `hsl(${a.hue}, 45%, 32%)`;
  const bar = isShot
    ? `<rect x="0" y="0" width="${w}" height="44" fill="#1f2937"/>
       <text x="${w / 2}" y="30" font-size="20" fill="#9ca3af" text-anchor="middle" font-family="sans-serif">9:41  ●●●</text>
       <rect x="24" y="80" width="${w - 48}" height="18" rx="9" fill="#374151"/>
       <rect x="24" y="112" width="${w - 96}" height="18" rx="9" fill="#374151"/>
       <rect x="24" y="144" width="${w - 72}" height="18" rx="9" fill="#374151"/>`
    : `<circle cx="${w * 0.7}" cy="${h * 0.3}" r="${h * 0.12}" fill="hsl(${a.hue}, 60%, 70%)" opacity="0.8"/>
       <path d="M0 ${h * 0.75} L ${w * 0.35} ${h * 0.45} L ${w * 0.6} ${h * 0.68} L ${w * 0.8} ${h * 0.52} L ${w} ${h * 0.66} L ${w} ${h} L 0 ${h} Z" fill="hsl(${a.hue}, 35%, 22%)"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${Math.round(w * scale)}" height="${Math.round(h * scale)}" viewBox="0 0 ${w} ${h}">
  <rect width="${w}" height="${h}" fill="${bg}"/>
  ${bar}
  <text x="${w / 2}" y="${h - 28}" font-size="26" fill="rgba(255,255,255,0.85)" text-anchor="middle" font-family="sans-serif">${a.label}</text>
</svg>`;
}

export function createMockImmich(): ImmichClient {
  const { assets, duplicates } = buildLibrary();
  const byId = new Map(assets.map((a) => [a.id, a]));
  const trashed = new Set<string>();

  return {
    mock: true,
    async ping() {
      return true;
    },
    async fetchAllAssets() {
      return assets.filter((a) => !trashed.has(a.id));
    },
    async getDuplicates() {
      return duplicates
        .map((g) => ({ ...g, assets: g.assets.filter((a) => !trashed.has(a.id)) }))
        .filter((g) => g.assets.length >= 2);
    },
    async trashAssets(ids) {
      for (const id of ids) trashed.add(id);
    },
    async restoreAssets(ids) {
      for (const id of ids) trashed.delete(id);
    },
    async setFavorite(id, isFavorite) {
      const a = byId.get(id);
      if (a) a.isFavorite = isFavorite;
    },
    async getThumbnail(id, size): Promise<Thumb> {
      const a = byId.get(id);
      const svg = a
        ? thumbnailSvg(a, size)
        : `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="#333"/></svg>`;
      const bytes = new TextEncoder().encode(svg);
      return { contentType: 'image/svg+xml', body: bytes.buffer as ArrayBuffer };
    },
  };
}
