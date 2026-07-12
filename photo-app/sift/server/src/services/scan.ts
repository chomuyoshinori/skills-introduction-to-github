import { getSetting, type Db } from '../db';
import type { ImmichAsset, ImmichClient } from '../immich/types';

// SPEC §6.1 スクリーンショット検出(Phase 1 はメタデータシグナルのみ。CLIP は Phase 2)
const SCREENSHOT_NAME_RE = /(screen[ _-]?shot|screenshot|スクリーンショット|スクショ)/i;

// 主要スマホの画面解像度(設定 device_resolutions で上書き可能)
export const DEFAULT_RESOLUTIONS = [
  '1179x2556', // iPhone 14 Pro / 15 / 15 Pro / 16
  '1170x2532', // iPhone 12 / 13 / 14
  '1290x2796', // iPhone 15 Pro Max / 16 Plus
  '1206x2622', // iPhone 16 Pro
  '1320x2868', // iPhone 16 Pro Max
  '1125x2436', // iPhone X / XS / 11 Pro
  '1080x2340',
  '1080x2400',
  '1440x3200',
  '1080x1920',
];

export interface ScanResult {
  scanned: number;
  screenshots: number;
  duplicateGroups: number;
}

export function screenshotScore(a: ImmichAsset, resolutions: Set<string>): number {
  let s = 0;
  if (SCREENSHOT_NAME_RE.test(a.originalFileName)) s += 0.5; // ファイル名(高)
  const exif = a.exifInfo;
  if (!exif?.make && !exif?.model) s += 0.2; // カメラ情報なし(中)
  const isPng = a.originalMimeType === 'image/png' || /\.png$/i.test(a.originalFileName);
  if (isPng) s += 0.15; // PNG(形式シグナルの一部)
  const w = exif?.exifImageWidth;
  const h = exif?.exifImageHeight;
  if (w && h && (resolutions.has(`${w}x${h}`) || resolutions.has(`${h}x${w}`))) s += 0.35; // 画面解像度一致(高)
  return Math.min(1, s);
}

async function importDuplicates(db: Db, immich: ImmichClient): Promise<number> {
  const groups = await immich.getDuplicates();
  const findGroup = db.prepare(`SELECT id FROM groups WHERE immich_ref = ?`);
  const insGroup = db.prepare(`INSERT INTO groups(kind, immich_ref, best_asset_id) VALUES('duplicate', ?, ?)`);
  const updBest = db.prepare(`UPDATE groups SET best_asset_id = ? WHERE id = ?`);
  const setMember = db.prepare(`UPDATE asset_state SET group_id = ? WHERE asset_id = ?`);

  const tx = db.transaction(() => {
    for (const g of groups) {
      if (!g.assets?.length) continue;
      const best = pickBest(g.assets);
      const row = findGroup.get(g.duplicateId) as { id: number } | undefined;
      let id: number;
      if (row) {
        id = row.id;
        updBest.run(best.id, id);
      } else {
        id = Number(insGroup.run(g.duplicateId, best.id).lastInsertRowid);
      }
      for (const a of g.assets) setMember.run(id, a.id);
    }
  });
  tx();
  return groups.length;
}

// 残す1枚の既定 = お気に入り > ファイルサイズ最大(Apple写真の「結合」に倣う。SPEC S-3)
function pickBest(assets: ImmichAsset[]): ImmichAsset {
  return [...assets].sort(
    (x, y) =>
      Number(y.isFavorite) - Number(x.isFavorite) ||
      (y.exifInfo?.fileSizeInByte ?? 0) - (x.exifInfo?.fileSizeInByte ?? 0)
  )[0];
}

export async function runScan(db: Db, immich: ImmichClient): Promise<ScanResult> {
  const resolutions = new Set<string>(
    JSON.parse(getSetting(db, 'device_resolutions', JSON.stringify(DEFAULT_RESOLUTIONS))) as string[]
  );
  const threshold = Number(getSetting(db, 'screenshot_threshold', '0.5'));

  const assets = await immich.fetchAllAssets();
  const upsert = db.prepare(`
    INSERT INTO asset_state (asset_id, category, score, file_name, taken_at, size_bytes, width, height, is_favorite, mime)
    VALUES (@asset_id, @category, @score, @file_name, @taken_at, @size_bytes, @width, @height, @is_favorite, @mime)
    ON CONFLICT(asset_id) DO UPDATE SET
      category = excluded.category,
      score = excluded.score,
      file_name = excluded.file_name,
      taken_at = excluded.taken_at,
      size_bytes = excluded.size_bytes,
      width = excluded.width,
      height = excluded.height,
      is_favorite = excluded.is_favorite,
      mime = excluded.mime
  `); // decision / group_id には触らない(ユーザーの判断を上書きしない)

  let screenshots = 0;
  const tx = db.transaction((rows: ImmichAsset[]) => {
    for (const a of rows) {
      const score = screenshotScore(a, resolutions);
      // お気に入りはセーフリスト(SPEC §6.4)— 候補に入れない
      const isShot = !a.isFavorite && score >= threshold;
      if (isShot) screenshots++;
      upsert.run({
        asset_id: a.id,
        category: isShot ? 'screenshot' : 'none',
        score,
        file_name: a.originalFileName,
        taken_at: a.localDateTime ?? a.fileCreatedAt,
        size_bytes: a.exifInfo?.fileSizeInByte ?? 0,
        width: a.exifInfo?.exifImageWidth ?? null,
        height: a.exifInfo?.exifImageHeight ?? null,
        is_favorite: a.isFavorite ? 1 : 0,
        mime: a.originalMimeType ?? null,
      });
    }
  });
  tx(assets);

  const duplicateGroups = await importDuplicates(db, immich);
  return { scanned: assets.length, screenshots, duplicateGroups };
}

// スキャンの同時実行ガード(起動時スキャンと手動スキャンの重複防止)
let inflight: Promise<ScanResult> | null = null;
export function runScanOnce(db: Db, immich: ImmichClient): Promise<ScanResult> {
  if (!inflight) {
    inflight = runScan(db, immich).finally(() => {
      inflight = null;
    });
  }
  return inflight;
}
