import type { DuplicateGroup, ImmichAsset, ImmichClient, Thumb } from './types';

// ─────────────────────────────────────────────────────────────
// Immich なしで UI/選別フローを試すためのモック(SIFT_MOCK=1)。
// スクショ24・重複5組・連写2組・類似3組・メモ書類8・ぼやけ5・通常25 のダミーライブラリ。
// サムネイルは決定論的に生成した SVG(連写・類似は同じ構図に微小ジッター、
// ぼやけは feGaussianBlur)なので、pHash・シャープネス解析の検証にも使える。
// ─────────────────────────────────────────────────────────────

// 乱数は再現性のためシード付き LCG
function lcg(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 2 ** 32;
  };
}

interface Scene {
  hue: number;
  sun: { x: number; y: number; r: number };
  peaks: number[]; // 山の高さ(0-1)×6点
  strokes: { x: number; y: number; dx: number; dy: number }[]; // テクスチャ(ぼかすと消える)
  blur: number; // feGaussianBlur の stdDeviation(0 = シャープ)
}

type Kind = 'photo' | 'shot' | 'doc';

interface MockAsset extends ImmichAsset {
  kind: Kind;
  scene: Scene | null;
  label: string;
  portrait: boolean;
}

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

function makeScene(rand: () => number, base?: Scene, blur = 0): Scene {
  if (base) {
    // 連写・類似用: 同じ構図に小さなジッター
    return {
      hue: base.hue,
      sun: { x: base.sun.x + (rand() - 0.5) * 30, y: base.sun.y + (rand() - 0.5) * 16, r: base.sun.r },
      peaks: base.peaks.map((p) => Math.min(0.95, Math.max(0.1, p + (rand() - 0.5) * 0.05))),
      strokes: base.strokes,
      blur,
    };
  }
  return {
    hue: Math.floor(rand() * 360),
    sun: { x: 120 + rand() * 400, y: 60 + rand() * 120, r: 30 + rand() * 40 },
    peaks: Array.from({ length: 6 }, () => 0.2 + rand() * 0.65),
    strokes: Array.from({ length: 36 }, () => ({
      x: rand() * 640,
      y: 180 + rand() * 280,
      dx: (rand() - 0.5) * 36,
      dy: (rand() - 0.5) * 24,
    })),
    blur,
  };
}

function buildLibrary(): { assets: MockAsset[]; duplicates: DuplicateGroup[]; memoIds: string[] } {
  const rand = lcg(20260712);
  const assets: MockAsset[] = [];
  const duplicates: DuplicateGroup[] = [];
  // 撮影日は 2026-06-20 起点で過去へ分散(決め打ちで再現性を保つ)
  const date = (daysAgo: number, h: number, m: number, s: number) =>
    new Date(Date.UTC(2026, 5, 20, h, m, s) - daysAgo * 86400_000).toISOString();
  const appleExif = { make: 'Apple', model: 'iPhone 15 Pro', exifImageWidth: 4032, exifImageHeight: 3024 };

  // ① スクリーンショット 24枚(PNG・EXIFなし・iPhone画面解像度)
  for (let i = 0; i < 24; i++) {
    const taken = date(Math.floor(rand() * 170), 9 + (i % 12), (i * 7) % 60, (i * 13) % 60);
    assets.push({
      id: `mock-shot-${i}`,
      originalFileName: `Screenshot_${taken.slice(0, 10)}-${pad(i)}.png`,
      originalMimeType: 'image/png',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: false,
      type: 'IMAGE',
      exifInfo: { fileSizeInByte: Math.round((0.8 + rand() * 2.7) * 1_000_000), exifImageWidth: 1179, exifImageHeight: 2556 },
      kind: 'shot',
      scene: null,
      label: `スクショ #${i + 1}`,
      portrait: true,
    });
  }

  // ② 完全重複 5組(同一シーン・サイズ違い)
  for (let g = 0; g < 5; g++) {
    const n = g % 2 === 0 ? 2 : 3;
    const scene = makeScene(rand);
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
        exifInfo: { ...appleExif, fileSizeInByte: Math.round((3 + k * 1.4 + rand()) * 1_000_000) },
        kind: 'photo',
        scene,
        label: `重複${g + 1}-${String.fromCharCode(65 + k)}`,
        portrait: false,
      });
    }
    assets.push(...members);
    duplicates.push({ duplicateId: `mock-dupgroup-${g}`, assets: members });
  }

  // ③ 連写 2組×4枚(2〜3秒間隔・同一カメラ・1枚はブレ)
  for (let g = 0; g < 2; g++) {
    const base = makeScene(rand);
    for (let k = 0; k < 4; k++) {
      const taken = date(5 + g * 3, 16, 20 + g * 5, k * 3);
      assets.push({
        id: `mock-burst-${g}-${k}`,
        originalFileName: `IMG_${4500 + g * 10 + k}.JPG`,
        originalMimeType: 'image/jpeg',
        fileCreatedAt: taken,
        localDateTime: taken,
        isFavorite: false,
        type: 'IMAGE',
        exifInfo: { ...appleExif, fileSizeInByte: Math.round((3.2 + rand() * 1.5) * 1_000_000) },
        kind: 'photo',
        scene: makeScene(rand, base, k === 2 ? 3 : 0), // 3枚目はブレ
        label: `連写${g + 1}-${k + 1}`,
        portrait: false,
      });
    }
  }

  // ④ 類似(撮り直し)3組×2枚(同日・25分間隔)
  for (let p = 0; p < 3; p++) {
    const base = makeScene(rand);
    for (let k = 0; k < 2; k++) {
      const taken = date(20 + p * 7, 11, 10 + k * 25, 0);
      assets.push({
        id: `mock-sim-${p}-${k}`,
        originalFileName: `IMG_${4700 + p * 10 + k}.JPG`,
        originalMimeType: 'image/jpeg',
        fileCreatedAt: taken,
        localDateTime: taken,
        isFavorite: false,
        type: 'IMAGE',
        exifInfo: { ...appleExif, fileSizeInByte: Math.round((2.8 + rand() * 2) * 1_000_000) },
        kind: 'photo',
        scene: makeScene(rand, base),
        label: `類似${p + 1}-${k + 1}`,
        portrait: false,
      });
    }
  }

  // ⑤ メモ写真(書類・ホワイトボード)8枚(60〜240日前 = 賞味期限切れ)
  for (let i = 0; i < 8; i++) {
    const taken = date(60 + i * 24, 13, (i * 9) % 60, 0);
    assets.push({
      id: `mock-memo-${i}`,
      originalFileName: `IMG_${4900 + i}.JPG`,
      originalMimeType: 'image/jpeg',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: false,
      type: 'IMAGE',
      exifInfo: { ...appleExif, fileSizeInByte: Math.round((1.8 + rand() * 1.8) * 1_000_000) },
      kind: 'doc',
      scene: null,
      label: i % 2 === 0 ? `書類メモ #${i + 1}` : `ホワイトボード #${i + 1}`,
      portrait: i % 3 === 0,
    });
  }

  // ⑥ ぼやけ写真 5枚(強いブラー)
  for (let i = 0; i < 5; i++) {
    const taken = date(8 + i * 11, 18, (i * 13) % 60, 0);
    assets.push({
      id: `mock-blur-${i}`,
      originalFileName: `IMG_${5000 + i}.JPG`,
      originalMimeType: 'image/jpeg',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: false,
      type: 'IMAGE',
      exifInfo: { ...appleExif, fileSizeInByte: Math.round((2.2 + rand() * 3) * 1_000_000) },
      kind: 'photo',
      scene: makeScene(rand, undefined, 6),
      label: `ぼやけ #${i + 1}`,
      portrait: false,
    });
  }

  // ⑧ RAW+JPEG ペア 2組(同ベース名・同時刻。判断のペア連動と類似グループ除外の確認用)
  for (let p = 0; p < 2; p++) {
    const scene = makeScene(rand);
    const taken = date(15 + p * 25, 10, 30 + p * 7, 0);
    for (const [ext, mime, mb] of [
      ['DNG', 'image/x-adobe-dng', 40 + p * 5],
      ['JPG', 'image/jpeg', 3.8 + p * 0.4],
    ] as const) {
      assets.push({
        id: `mock-raw-${p}-${ext.toLowerCase()}`,
        originalFileName: `IMG_${6001 + p}.${ext}`,
        originalMimeType: mime,
        fileCreatedAt: taken,
        localDateTime: taken,
        isFavorite: false,
        type: 'IMAGE',
        exifInfo: { ...appleExif, fileSizeInByte: Math.round(mb * 1_000_000) },
        kind: 'photo',
        scene,
        label: `RAWペア${p + 1} (${ext})`,
        portrait: false,
      });
    }
  }

  // ⑨ 動画: 画面収録 3本(EXIFなし・名前パターン)+ カメラ動画 3本(1本は200MB未満)
  const screenRecs: [string, number, string][] = [
    ['ScreenRecording_2026-04-02-09-12-33.mp4', 130, '00:01:45.000'],
    ['RPReplay_Final1770000001.MP4', 280, '00:04:12.000'],
    ['ScreenRecording_2026-02-14-20-01-05.mp4', 95, '00:00:32.000'],
  ];
  screenRecs.forEach(([name, mb, dur], i) => {
    const taken = date(30 + i * 40, 9 + i, i * 17, 0);
    assets.push({
      id: `mock-screc-${i}`,
      originalFileName: name,
      originalMimeType: 'video/mp4',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: false,
      type: 'VIDEO',
      duration: dur,
      exifInfo: { fileSizeInByte: Math.round(mb * 1_000_000) },
      kind: 'shot',
      scene: null,
      label: `画面収録 #${i + 1}`,
      portrait: true,
    });
  });
  const camVideos: [number, string][] = [
    [90, '00:00:58.000'],
    [250, '00:03:21.000'],
    [850, '00:21:37.000'],
  ];
  camVideos.forEach(([mb, dur], i) => {
    const taken = date(12 + i * 30, 15, i * 13, 0);
    assets.push({
      id: `mock-video-${i}`,
      originalFileName: `IMG_${7001 + i}.MOV`,
      originalMimeType: 'video/quicktime',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: false,
      type: 'VIDEO',
      duration: dur,
      exifInfo: { ...appleExif, fileSizeInByte: Math.round(mb * 1_000_000) },
      kind: 'photo',
      scene: makeScene(rand),
      label: `動画 #${i + 1} (${mb}MB)`,
      portrait: false,
    });
  });

  // ⑦ 通常写真 25枚(うち2枚はお気に入り → 候補除外の確認用)
  for (let i = 0; i < 25; i++) {
    const taken = date(Math.floor(rand() * 300), 8 + (i % 10), (i * 3) % 60, (i * 17) % 60);
    assets.push({
      id: `mock-photo-${i}`,
      originalFileName: `IMG_${5200 + i}.JPG`,
      originalMimeType: 'image/jpeg',
      fileCreatedAt: taken,
      localDateTime: taken,
      isFavorite: i === 3 || i === 17,
      type: 'IMAGE',
      exifInfo: { ...appleExif, fileSizeInByte: Math.round((2.5 + rand() * 5.5) * 1_000_000) },
      kind: 'photo',
      scene: makeScene(rand),
      label: `写真 #${i + 1}`,
      portrait: rand() < 0.3,
    });
  }

  // CLIP は完璧ではないので 8枚中6枚だけヒットさせる(残りはヒューリスティックで拾う)
  const memoIds = ['mock-memo-0', 'mock-memo-1', 'mock-memo-2', 'mock-memo-3', 'mock-memo-4', 'mock-memo-5'];
  return { assets, duplicates, memoIds };
}

function photoSvg(a: MockAsset, w: number, h: number): string {
  const s = a.scene!;
  const n = s.peaks.length;
  const pts = s.peaks.map((p, i) => `L ${Math.round((i * w) / (n - 1))} ${Math.round(h * (1 - p * 0.55))}`).join(' ');
  const strokes = s.strokes
    .map(
      (t) =>
        `<line x1="${(t.x / 640) * w}" y1="${(t.y / 480) * h}" x2="${((t.x + t.dx) / 640) * w}" y2="${((t.y + t.dy) / 480) * h}" stroke="rgba(255,255,255,0.35)" stroke-width="2"/>`
    )
    .join('');
  const blurFilter = s.blur > 0 ? `<filter id="b"><feGaussianBlur stdDeviation="${s.blur}"/></filter>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  ${blurFilter}
  <g ${s.blur > 0 ? 'filter="url(#b)"' : ''}>
    <rect width="${w}" height="${h}" fill="hsl(${s.hue}, 42%, 34%)"/>
    <circle cx="${(s.sun.x / 640) * w}" cy="${(s.sun.y / 480) * h}" r="${(s.sun.r / 640) * w}" fill="hsl(${s.hue}, 65%, 72%)"/>
    <path d="M0 ${h} L 0 ${Math.round(h * (1 - s.peaks[0] * 0.55))} ${pts} L ${w} ${h} Z" fill="hsl(${s.hue}, 35%, 18%)"/>
    ${strokes}
    <text x="${w / 2}" y="${h - 16}" font-size="22" fill="rgba(255,255,255,0.9)" text-anchor="middle" font-family="sans-serif">${a.label}</text>
  </g>
</svg>`;
}

function docSvg(a: MockAsset, w: number, h: number, rand: () => number): string {
  const rows: string[] = [];
  const rowH = Math.round(h / 16);
  for (let i = 0; i < 12; i++) {
    const width = (0.5 + rand() * 0.42) * (w - 48);
    const y = Math.round(rowH * (1.5 + i * 1.15));
    rows.push(`<rect x="24" y="${y}" width="${Math.round(width)}" height="${Math.round(rowH * 0.5)}" fill="#2f2f2f"/>`);
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <rect width="${w}" height="${h}" fill="#f4f2ec"/>
  ${rows.join('')}
  <text x="${w / 2}" y="${h - 14}" font-size="18" fill="#8a8a8a" text-anchor="middle" font-family="sans-serif">${a.label}</text>
</svg>`;
}

function shotSvg(a: MockAsset, w: number, h: number): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <rect width="${w}" height="${h}" fill="#111827"/>
  <rect x="0" y="0" width="${w}" height="44" fill="#1f2937"/>
  <text x="${w / 2}" y="30" font-size="20" fill="#9ca3af" text-anchor="middle" font-family="sans-serif">9:41  ●●●</text>
  <rect x="24" y="80" width="${w - 48}" height="18" rx="9" fill="#374151"/>
  <rect x="24" y="112" width="${w - 96}" height="18" rx="9" fill="#374151"/>
  <rect x="24" y="144" width="${w - 72}" height="18" rx="9" fill="#374151"/>
  <text x="${w / 2}" y="${h - 28}" font-size="26" fill="rgba(255,255,255,0.85)" text-anchor="middle" font-family="sans-serif">${a.label}</text>
</svg>`;
}

function thumbnailSvg(a: MockAsset, size: 'thumbnail' | 'preview'): string {
  const scale = size === 'thumbnail' ? 0.5 : 1;
  const w = Math.round((a.portrait ? 360 : 640) * scale);
  const h = Math.round((a.portrait ? 780 : 480) * scale);
  let svg: string;
  if (a.kind === 'shot') svg = shotSvg(a, w, h);
  else if (a.kind === 'doc') svg = docSvg(a, w, h, lcg(a.id.length * 7919 + a.id.charCodeAt(a.id.length - 1)));
  else svg = photoSvg(a, w, h);
  if (a.type === 'VIDEO') {
    // 再生マークを重ねて動画サムネらしくする
    const play = `<circle cx="${w / 2}" cy="${h / 2}" r="${Math.round(w * 0.09)}" fill="rgba(0,0,0,0.55)"/>
  <path d="M ${w / 2 - w * 0.03} ${h / 2 - w * 0.045} L ${w / 2 + w * 0.055} ${h / 2} L ${w / 2 - w * 0.03} ${h / 2 + w * 0.045} Z" fill="#fff"/>`;
    svg = svg.replace('</svg>', `${play}</svg>`);
  }
  return svg;
}

export function createMockImmich(): ImmichClient {
  const { assets, duplicates, memoIds } = buildLibrary();
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
    async smartSearch(query) {
      if (/document|receipt|whiteboard|note|price/i.test(query)) return memoIds.filter((id) => !trashed.has(id));
      if (/screenshot/i.test(query)) return assets.filter((a) => a.kind === 'shot' && !trashed.has(a.id)).map((a) => a.id);
      return [];
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
