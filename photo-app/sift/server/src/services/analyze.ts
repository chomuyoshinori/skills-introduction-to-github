import sharp from 'sharp';
import { getSetting, type Db } from '../db';
import type { ImmichClient } from '../immich/types';
import { runScan, type ScanResult } from './scan';

// ─────────────────────────────────────────────────────────────
// Phase 2: 画像解析(SPEC §6.2, §6.3)
//  - pHash(dHash 64bit)      → 類似グループ化
//  - シャープネス(ラプラシアン分散) → ぼやけ検出・ベストショット提案
//  - 書類ヒューリスティック      → メモ写真検出(低彩度・白背景・高エッジ密度)
//  - CLIP スマート検索          → メモ写真検出(Immich の ML を利用)
// 解析はサムネイル(小)1枚の取得だけで行い、原本には触れない。
// ─────────────────────────────────────────────────────────────

const MEMO_QUERIES = ['document', 'receipt', 'whiteboard', 'handwritten note', 'price tag'];
const ANALYZE_CONCURRENCY = 8;

interface Metrics {
  phash: string;
  sharpness: number;
  docLike: 0 | 1;
}

export async function computeMetrics(buf: ArrayBuffer): Promise<Metrics> {
  const { data, info } = await sharp(Buffer.from(buf))
    .resize(64, 64, { fit: 'fill' })
    .removeAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  const w = 64;
  const h = 64;
  const ch = info.channels;

  const grey = new Float64Array(w * h);
  let whiteCount = 0;
  let satSum = 0;
  for (let i = 0; i < w * h; i++) {
    const r = data[i * ch];
    const g = data[i * ch + 1];
    const b = data[i * ch + 2];
    const y = 0.299 * r + 0.587 * g + 0.114 * b;
    grey[i] = y;
    if (y > 225) whiteCount++;
    const mx = Math.max(r, g, b);
    satSum += mx === 0 ? 0 : (mx - Math.min(r, g, b)) / mx;
  }

  // ラプラシアン: 分散 = シャープネス、|平均| = エッジ密度
  let sum = 0;
  let sum2 = 0;
  let absSum = 0;
  let n = 0;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      const v = grey[i - 1] + grey[i + 1] + grey[i - w] + grey[i + w] - 4 * grey[i];
      sum += v;
      sum2 += v * v;
      absSum += Math.abs(v);
      n++;
    }
  }
  const mean = sum / n;
  const sharpness = sum2 / n - mean * mean;
  const edgeDensity = absSum / n;
  const whiteness = whiteCount / (w * h);
  const saturation = satSum / (w * h);
  // 書類・ホワイトボードらしさ: 低彩度 + 白背景 + 文字由来の高エッジ
  const docLike: 0 | 1 = saturation < 0.2 && whiteness > 0.35 && edgeDensity > 6 ? 1 : 0;

  // dHash: 64x64 グレイを 9x8 にブロック平均 → 隣接比較で 64bit
  const gw = 9;
  const gh = 8;
  const g2 = new Float64Array(gw * gh);
  for (let gy = 0; gy < gh; gy++) {
    for (let gx = 0; gx < gw; gx++) {
      let s = 0;
      let c = 0;
      const x0 = Math.floor((gx * w) / gw);
      const x1 = Math.floor(((gx + 1) * w) / gw);
      const y0 = Math.floor((gy * h) / gh);
      const y1 = Math.floor(((gy + 1) * h) / gh);
      for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) { s += grey[y * w + x]; c++; }
      g2[gy * gw + gx] = s / c;
    }
  }
  let bits = 0n;
  for (let gy = 0; gy < 8; gy++) {
    for (let gx = 0; gx < 8; gx++) {
      bits = (bits << 1n) | (g2[gy * gw + gx] < g2[gy * gw + gx + 1] ? 1n : 0n);
    }
  }
  const phash = bits.toString(16).padStart(16, '0');

  return { phash, sharpness, docLike };
}

export function hamming(a: string, b: string): number {
  let x = BigInt('0x' + a) ^ BigInt('0x' + b);
  let c = 0;
  while (x) {
    c += Number(x & 1n);
    x >>= 1n;
  }
  return c;
}

async function pool<T>(items: T[], n: number, fn: (t: T) => Promise<void>): Promise<void> {
  let i = 0;
  await Promise.all(
    Array.from({ length: Math.min(n, items.length) }, async () => {
      while (i < items.length) {
        const item = items[i++];
        await fn(item);
      }
    })
  );
}

/** 未解析アセットのサムネイルを取得して pHash・シャープネス・書類度を計算(増分) */
export async function analyzeAssets(db: Db, immich: ImmichClient): Promise<{ analyzed: number; failed: number }> {
  const rows = db
    .prepare(`SELECT asset_id FROM asset_state WHERE phash IS NULL AND (decision IS NULL OR decision != 'trashed')`)
    .all() as { asset_id: string }[];
  const upd = db.prepare(`UPDATE asset_state SET phash = ?, sharpness = ?, doc_like = ? WHERE asset_id = ?`);
  let analyzed = 0;
  let failed = 0;
  await pool(rows, ANALYZE_CONCURRENCY, async (r) => {
    try {
      const t = await immich.getThumbnail(r.asset_id, 'thumbnail');
      const m = await computeMetrics(t.body);
      upd.run(m.phash, m.sharpness, m.docLike, r.asset_id);
      analyzed++;
    } catch {
      failed++; // 次回の解析で再試行される
    }
  });
  return { analyzed, failed };
}

/** Immich の CLIP スマート検索でメモ系ワードにヒットしたアセットへ印を付ける */
export async function refreshClipHits(db: Db, immich: ImmichClient): Promise<number> {
  const ids = new Set<string>();
  try {
    for (const q of MEMO_QUERIES) {
      for (const id of await immich.smartSearch(q)) ids.add(id);
    }
  } catch {
    return -1; // スマート検索が使えない環境ではヒューリスティックのみで判定
  }
  const setOne = db.prepare(`UPDATE asset_state SET memo_clip = 1 WHERE asset_id = ?`);
  const tx = db.transaction(() => {
    db.prepare(`UPDATE asset_state SET memo_clip = 0`).run();
    for (const id of ids) setOne.run(id);
  });
  tx();
  return ids.size;
}

/** 解析結果からカテゴリ(memo / blurry)を付け直す。screenshot はスキャン側の判定を優先 */
export function categorize(db: Db): { memo: number; blurry: number } {
  // 64x64 サムネイルのラプラシアン分散: 強いブレは 50 未満、鮮明な写真は数百以上に分かれる
  const blurTh = Number(getSetting(db, 'blur_threshold', '60'));
  const memoTh = Number(getSetting(db, 'memo_threshold', '0.5'));
  const ageDaysTh = Number(getSetting(db, 'memo_age_days', '30'));
  const now = Date.now();

  const rows = db
    .prepare(
      `SELECT asset_id, taken_at, sharpness, doc_like, memo_clip FROM asset_state
       WHERE category != 'screenshot' AND (decision IS NULL OR decision != 'trashed')`
    )
    .all() as { asset_id: string; taken_at: string | null; sharpness: number | null; doc_like: number; memo_clip: number }[];
  const upd = db.prepare(`UPDATE asset_state SET category = ?, score = ? WHERE asset_id = ?`);

  let memo = 0;
  let blurry = 0;
  const tx = db.transaction(() => {
    for (const r of rows) {
      const ageDays = r.taken_at ? (now - Date.parse(r.taken_at)) / 86_400_000 : 0;
      // SPEC §6.2: CLIP(中 0.4)+ 書類ヒューリスティック(0.35)+ 経過日数(中 0.15)
      const memoScore = (r.memo_clip ? 0.4 : 0) + (r.doc_like ? 0.35 : 0) + (ageDays > ageDaysTh ? 0.15 : 0);
      if (memoScore >= memoTh) {
        upd.run('memo', memoScore, r.asset_id);
        memo++;
      } else if (r.sharpness != null && r.sharpness < blurTh) {
        upd.run('blurry', Math.min(1, 1 - r.sharpness / blurTh), r.asset_id);
        blurry++;
      } else {
        upd.run('none', 0, r.asset_id);
      }
    }
  });
  tx();
  return { memo, blurry };
}

/** 連写(±N秒・同一カメラ)と類似(同日内 pHash 距離)のグループを作り直す */
export function buildGroups(db: Db): { burstGroups: number; similarGroups: number } {
  const gapSec = Number(getSetting(db, 'burst_gap_seconds', '5'));
  const hammingTh = Number(getSetting(db, 'similar_hamming', '10'));

  // burst/similar は毎回作り直す(判断はアセット側に残るので安全)。duplicate は保持
  db.exec(`
    UPDATE asset_state SET group_id = NULL
    WHERE group_id IN (SELECT id FROM groups WHERE kind IN ('burst','similar'));
    DELETE FROM groups WHERE kind IN ('burst','similar');
  `);

  // スクショ・メモは専用キューがあるためグループ化対象から外す
  const rows = db
    .prepare(
      `SELECT asset_id, taken_at, camera, phash, group_id FROM asset_state
       WHERE (decision IS NULL OR decision != 'trashed') AND phash IS NOT NULL
         AND category NOT IN ('screenshot', 'memo')
       ORDER BY taken_at`
    )
    .all() as { asset_id: string; taken_at: string | null; camera: string | null; phash: string; group_id: number | null }[];

  const insGroup = db.prepare(`INSERT INTO groups(kind, best_asset_id) VALUES(?, ?)`);
  const setMember = db.prepare(`UPDATE asset_state SET group_id = ? WHERE asset_id = ?`);
  const assigned = new Set<string>(rows.filter((r) => r.group_id != null).map((r) => r.asset_id));

  function createGroup(kind: 'burst' | 'similar', memberIds: string[]): void {
    const id = Number(insGroup.run(kind, memberIds[0]).lastInsertRowid);
    for (const m of memberIds) {
      setMember.run(id, m);
      assigned.add(m);
    }
  }

  // 連写: 同一カメラ・撮影間隔 gapSec 以内のチェーン
  let burstGroups = 0;
  let chain: typeof rows = [];
  const flushChain = () => {
    if (chain.length >= 2) {
      createGroup('burst', chain.map((c) => c.asset_id));
      burstGroups++;
    }
    chain = [];
  };
  const txBurst = db.transaction(() => {
    for (const r of rows) {
      if (assigned.has(r.asset_id) || !r.camera || !r.taken_at) {
        flushChain();
        continue;
      }
      const prev = chain[chain.length - 1];
      if (prev && prev.camera === r.camera && Date.parse(r.taken_at) - Date.parse(prev.taken_at!) <= gapSec * 1000) {
        chain.push(r);
      } else {
        flushChain();
        chain.push(r);
      }
    }
    flushChain();
  });
  txBurst();

  // 類似: 同日バケット内で pHash のハミング距離 ≤ しきい値 を Union-Find で結合
  const byDay = new Map<string, typeof rows>();
  for (const r of rows) {
    if (assigned.has(r.asset_id) || !r.taken_at) continue;
    const day = r.taken_at.slice(0, 10);
    byDay.set(day, [...(byDay.get(day) ?? []), r]);
  }

  let similarGroups = 0;
  const txSim = db.transaction(() => {
    for (const bucket of byDay.values()) {
      if (bucket.length < 2 || bucket.length > 800) continue; // 異常な日は総当たりを避ける
      const parent = bucket.map((_, i) => i);
      const find = (i: number): number => (parent[i] === i ? i : (parent[i] = find(parent[i])));
      for (let i = 0; i < bucket.length; i++) {
        for (let j = i + 1; j < bucket.length; j++) {
          if (hamming(bucket[i].phash, bucket[j].phash) <= hammingTh) parent[find(i)] = find(j);
        }
      }
      const comps = new Map<number, string[]>();
      for (let i = 0; i < bucket.length; i++) {
        const root = find(i);
        comps.set(root, [...(comps.get(root) ?? []), bucket[i].asset_id]);
      }
      for (const ids of comps.values()) {
        if (ids.length >= 2) {
          createGroup('similar', ids);
          similarGroups++;
        }
      }
    }
  });
  txSim();

  return { burstGroups, similarGroups };
}

/** 全グループのベスト(★)を再計算。お気に入り > (重複はサイズ / 連写・類似はシャープネス) */
export function recomputeBest(db: Db): void {
  const groups = db.prepare(`SELECT id, kind FROM groups`).all() as { id: number; kind: string }[];
  const membersStmt = db.prepare(
    `SELECT asset_id, is_favorite, sharpness, size_bytes FROM asset_state
     WHERE group_id = ? AND (decision IS NULL OR decision != 'trashed')`
  );
  const upd = db.prepare(`UPDATE groups SET best_asset_id = ? WHERE id = ?`);
  for (const g of groups) {
    const ms = membersStmt.all(g.id) as { asset_id: string; is_favorite: number; sharpness: number | null; size_bytes: number }[];
    if (!ms.length) continue;
    const best = [...ms].sort(
      (x, y) =>
        y.is_favorite - x.is_favorite ||
        (g.kind === 'duplicate'
          ? y.size_bytes - x.size_bytes
          : (y.sharpness ?? -1) - (x.sharpness ?? -1) || y.size_bytes - x.size_bytes)
    )[0];
    upd.run(best.asset_id, g.id);
  }
}

export interface FullScanResult extends ScanResult {
  analyzed: number;
  analyzeFailed: number;
  clipHits: number;
  memo: number;
  blurry: number;
  burstGroups: number;
  similarGroups: number;
}

export async function runFullScan(db: Db, immich: ImmichClient): Promise<FullScanResult> {
  const scan = await runScan(db, immich); // メタデータ + スクショ判定 + 重複取り込み
  const a = await analyzeAssets(db, immich); // サムネイル解析(増分)
  const clipHits = await refreshClipHits(db, immich);
  const cats = categorize(db);
  const g = buildGroups(db);
  recomputeBest(db);
  return { ...scan, analyzed: a.analyzed, analyzeFailed: a.failed, clipHits, ...cats, ...g };
}

// スキャン全体の同時実行ガード(起動時と手動実行の重複防止)
let inflight: Promise<FullScanResult> | null = null;
export function runFullScanOnce(db: Db, immich: ImmichClient): Promise<FullScanResult> {
  if (!inflight) {
    inflight = runFullScan(db, immich).finally(() => {
      inflight = null;
    });
  }
  return inflight;
}
